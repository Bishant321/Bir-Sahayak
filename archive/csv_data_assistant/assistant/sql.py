"""Conservative SELECT validation and resource-limited local execution."""
import json
from threading import Timer

import duckdb
import sqlglot
from sqlglot import exp

from assistant.config import CONFIG

# Only analytical functions required by this application are exposed.
FUNCTIONS = {
    "ABS", "AVG", "CEIL", "CEILING", "COALESCE", "COUNT", "FLOOR", "GREATEST",
    "LEAST", "LOWER", "UPPER", "LENGTH", "MAX", "MIN", "MEDIAN", "NULLIF",
    "ROUND", "STDDEV", "STDDEV_SAMP", "STDDEV_POP", "SUM", "VARIANCE",
    "VAR_POP", "CAST", "TRY_CAST", "EXTRACT", "DATE_TRUNC", "TIMESTAMP_TRUNC",
    "TRIM", "SUBSTRING", "CONCAT", "CASE", "IF", "ROW_NUMBER", "RANK",
    "DENSE_RANK", "LAG", "LEAD", "PERCENTILE_CONT", "QUANTILE_CONT",
}


def validate_sql(query: str) -> str:
    if not isinstance(query, str) or not query.strip() or len(query) > 10000:
        raise ValueError("Enter a SELECT query of at most 10,000 characters.")
    try:
        statements = sqlglot.parse(query, read="duckdb")
    except (sqlglot.errors.SqlglotError, RecursionError) as exc:
        raise ValueError("The SQL query could not be parsed.") from exc
    if len(statements) != 1 or not isinstance(statements[0], exp.Select):
        raise ValueError("Only a single read-only SELECT statement is allowed.")
    tree = statements[0]
    forbidden = (exp.DDL, exp.DML, exp.Command, exp.Into, exp.Lock)
    if any(isinstance(node, forbidden) for node in tree.walk()):
        raise ValueError("The query contains an operation that is not read-only.")
    if any(node.args.get("recursive") for node in tree.find_all(exp.With)):
        raise ValueError("Recursive queries are not supported.")
    ctes = {cte.alias.lower() for cte in tree.find_all(exp.CTE)}
    for cte in tree.find_all(exp.CTE):
        if not isinstance(cte.this, exp.Select):
            raise ValueError("Common table expressions must contain a SELECT.")
    for table in tree.find_all(exp.Table):
        if (not isinstance(table.this, exp.Identifier) or table.db or table.catalog
                or table.name.lower() not in {"dataset", *ctes}):
            raise ValueError("Queries may only read the uploaded table named dataset.")
    for func in tree.find_all(exp.Func):
        name = func.name.upper() if isinstance(func, exp.Anonymous) else func.sql_name()
        if name not in FUNCTIONS:
            raise ValueError(f"SQL function {name} is not supported.")
    return tree.sql(dialect="duckdb")


def run_sql(frame, query: str) -> dict:
    normalized = validate_sql(query)
    limit = CONFIG["data"]["sql_result_rows"]
    connection = duckdb.connect(":memory:", config={
        "enable_external_access": "false", "autoload_known_extensions": "false",
        "autoinstall_known_extensions": "false", "threads": "2", "memory_limit": "256MB",
    })
    timer = None
    try:
        connection.register("dataset", frame)
        timer = Timer(CONFIG["data"]["sql_timeout_seconds"], connection.interrupt)
        timer.daemon = True
        timer.start()
        result = connection.execute(
            f'SELECT * FROM ({normalized}) AS "answer" LIMIT {limit + 1}'
        ).fetchdf()
        truncated = len(result) > limit
        result = result.head(limit)
        # Column arrays preserve duplicate SQL output labels without losing values.
        values = json.loads(result.to_json(orient="split", date_format="iso"))["data"]
        return {"sql": normalized, "columns": list(result.columns), "rows": values,
                "returned_rows": len(result), "truncated": truncated,
                "note": f"At most {limit} result rows are displayed; calculations use the full dataset."}
    except duckdb.Error as exc:
        raise ValueError(f"SQL could not run: {str(exc)[:500]}") from exc
    finally:
        if timer:
            timer.cancel()
            timer.join()
        connection.close()
