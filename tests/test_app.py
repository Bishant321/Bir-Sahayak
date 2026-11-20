from streamlit.testing.v1 import AppTest

from studentbank.settings import ROOT
from studentbank import speech


def test_dashboard_and_single_prediction():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not app.exception
    assert app.title[0].value == "Make sense of your spending."
    assert app.metric[1].value == "400"
    next(button for button in app.button if button.label == "Predict category").click().run()
    assert not app.exception
    assert app.session_state["studentbank_prediction"][1]["predicted_category"] == "groceries"
    app.checkbox[0].check().run()
    assert not app.exception


def test_voice_generation_and_stale_audio_removal(monkeypatch):
    monkeypatch.setattr(speech, "speech_engine", lambda: ("test voice", "/fake/voice"))
    monkeypatch.setattr(speech, "synthesise", lambda text: b"test audio")
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    next(button for button in app.button if button.label == "Generate spoken summary").click().run()
    assert not app.exception
    assert app.session_state["speech_audio"] == b"test audio"
    assert not app.get("audio")[0].proto.autoplay
    raw = b"transaction_id,date,description,amount_gbp,currency\none,2026-09-01,Tesco weekly groceries,1.01,GBP\n"
    app.session_state["studentbank_source"] = (raw, "one transaction")
    app.run()
    assert not app.exception
    assert len(app.get("audio")) == 0
    assert "totalling 1 pound and 1 penny" in app.session_state["speech_text"]
