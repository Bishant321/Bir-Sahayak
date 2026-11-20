import pandas as pd
import pytest

from assistant.data import Dataset
from assistant.sql import run_sql, validate_sql


@pytest.mark.parametrize("query", [
    "DROP TABLE dataset", "DELETE FROM dataset", "UPDATE dataset SET id=1",
    "SELECT * FROM dataset; SELECT 1", "SELECT * FROM read_csv_auto('/etc/passwd')",
    "SELECT * FROM '/etc/passwd'", "SELECT * FROM information_schema.tables",
    "SELECT * FROM sqlite_scan('x', 'y')", "SELECT * FROM range(1000000000)",
    "SELECT getenv('SECRET')", "SELECT current_setting('home_directory')",
    "SELECT * FROM query('SELECT 1')", "COPY dataset TO '/tmp/out.csv'",
    "INSTALL httpfs", "ATTACH '/tmp/x.db'", "PRAGMA version",
    "SELECT * INTO secret FROM dataset", "SELECT repeat('a', 1000000000)",
    "WITH RECURSIVE t AS (SELECT 1 UNION ALL SELECT * FROM t) SELECT * FROM t",
    "WITH t AS (DELETE FROM dataset RETURNING *) SELECT * FROM t",
    "SELECT * FROM dataset UNION SELECT * FROM dataset",
    "SELECT 'unterminated", "SELECT ( FROM dataset",
])
def test_rejects_unsafe_or_unsupported_sql(query):
    with pytest.raises(ValueError):
        validate_sql(query)


def test_verified_aggregate_and_cte_do_not_change_data():
    data = Dataset(b"region,revenue\nNorth,10\nSouth,20\nNorth,30\n")
    before = data.frame.copy(deep=True)
    result = data.query_sql('WITH totals AS (SELECT region, SUM(revenue) AS total FROM dataset GROUP BY region) SELECT * FROM totals ORDER BY total DESC')
    assert result["rows"] == [["North", 40], ["South", 20]]
    pd.testing.assert_frame_equal(data.frame, before)
    assert not data.history


def test_results_limited_without_limiting_calculation():
    frame = pd.DataFrame({"n": range(100)})
    assert run_sql(frame, "SELECT SUM(n) FROM dataset")["rows"] == [[4950]]
    result = run_sql(frame, "SELECT n FROM dataset ORDER BY n")
    assert result["truncated"] and result["returned_rows"] == 50


def test_missing_column_and_null_output():
    frame = pd.DataFrame({"n": [1, None]})
    with pytest.raises(ValueError, match="SQL could not run"):
        run_sql(frame, "SELECT nonexistent FROM dataset")
    assert run_sql(frame, "SELECT n FROM dataset WHERE n IS NULL")["rows"] == [[None]]


def test_sql_duplicate_labels_remain_inspectable():
    result = run_sql(pd.DataFrame({"n": [1]}), "SELECT n AS a, n+1 AS a FROM dataset")
    assert result["rows"] == [[1, 2]]


def test_comment_and_quoted_column():
    result = run_sql(pd.DataFrame({"order value": [5, 7]}), '-- total\nSELECT SUM("order value") AS total FROM dataset;')
    assert result["rows"] == [[12]]
