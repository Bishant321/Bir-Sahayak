import pytest

from studentbank.transactions import load_transactions, parse_pence, pounds, summarise

HEADER = b"transaction_id,date,description,amount_gbp,currency\n"


@pytest.mark.parametrize("value,expected", [("0.01", 1), ("12.30", 1230), ("1000000.00", 100000000), ("0.1", 10)])
def test_exact_money(value, expected):
    assert parse_pence(value) == expected


@pytest.mark.parametrize("value", ["0", "-3", "NaN", "Infinity", "0.001", "1e3", "£2", "1000000.01", ""])
def test_invalid_money(value):
    with pytest.raises(ValueError):
        parse_pence(value)


def test_summary_exact_and_review_included():
    frame = load_transactions(HEADER + b"01,2026-09-01,food,0.10,GBP\n02,2026-09-02,bus,0.20,GBP\n")
    frame["display_category"] = ["groceries", "needs review"]
    frame["needs_review"] = [False, True]
    result = summarise(frame)
    assert result["total_pence"] == 30
    assert result["by_category_pence"] == {"groceries": 10, "needs review": 20}
    assert "£0.30" in result["announcement_text"]
    assert frame.transaction_id.tolist() == ["01", "02"]
    assert pounds(123456) == "£1,234.56"


@pytest.mark.parametrize("row", [b"1,2026-02-30,food,2,GBP\n", b"1,2026-09-01,food,2,USD\n",
                                   b"1,2026-09-01,,2,GBP\n", b"1,2026-09-01,food,-2,GBP\n",
                                   b"1,2026-09-01,food,2,GBP,extra\n", b"1,2026-09-01,food,2\n"])
def test_bad_csv_rows(row):
    with pytest.raises(ValueError):
        load_transactions(HEADER + row)


def test_duplicate_ids_empty_and_non_utf8():
    for raw in [HEADER, b"\xff", HEADER + b"1,2026-09-01,a,1,GBP\n1,2026-09-02,b,1,GBP\n"]:
        with pytest.raises(ValueError):
            load_transactions(raw)
