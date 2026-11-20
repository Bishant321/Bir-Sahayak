from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def button(app, label):
    return next(item for item in app.button if item.label == label)


def test_sample_inspect_clean_undo_and_sql():
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    assert not app.exception
    button(app, "Try the sample dataset").click().run()
    assert not app.exception
    assert app.metric[0].value == "21"
    button(app, "Find missing values").click().run()
    assert app.session_state["messages"][-1]["results"][0].data["total_missing"] == 5
    button(app, "Remove duplicates").click().run()
    assert app.metric[0].value == "20"
    button(app, "Undo last change").click().run()
    assert app.metric[0].value == "21"
    button(app, "Run query").click().run()
    assert app.session_state["messages"][-1]["results"][0].data["rows"] == [[21]]
    assert not app.exception
