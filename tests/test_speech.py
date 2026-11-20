from io import BytesIO
import subprocess
import wave

import pytest

from studentbank import speech


@pytest.mark.parametrize("pence, expected", [(0, "0 pounds"), (1, "1 penny"),
    (25, "25 pence"), (100, "1 pound"), (101, "1 pound and 1 penny"),
    (2208225, "22082 pounds and 25 pence")])
def test_spoken_money(pence, expected):
    assert speech.spoken_gbp(pence) == expected


def test_summary_preserves_review_and_exact_totals():
    text = speech.announcement({"transaction_count": 2, "start_date": "2026-09-01",
        "end_date": "2026-09-02", "total_pence": 101, "needs_review": 1,
        "by_category_pence": {"groceries": 100, "needs review": 1}})
    assert "totalling 1 pound and 1 penny" in text
    assert "groceries, at 1 pound" in text
    assert "1 transaction needs a category review" in text
    assert "1 September 2026" in text
    assert "model estimates" in text
    assert speech.announcement({"transaction_count": 0}) == "There are no outgoing transactions to summarise."


def test_missing_engine(monkeypatch):
    monkeypatch.setattr(speech, "speech_engine", lambda: None)
    with pytest.raises(RuntimeError, match="No offline speech engine"):
        speech.synthesise("Spending summary.")


def test_engine_timeout(monkeypatch):
    monkeypatch.setattr(speech, "speech_engine", lambda: ("eSpeak", "/fake/espeak"))
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 60)
    monkeypatch.setattr(speech.subprocess, "run", timeout)
    with pytest.raises(RuntimeError, match="timed out"):
        speech.synthesise("Spending summary.")


def test_wav_generation_and_cleanup(monkeypatch):
    monkeypatch.setattr(speech, "speech_engine", lambda: ("eSpeak", "/fake/espeak"))
    paths = []
    def generate(command, **kwargs):
        assert kwargs["input"] == "1 pound and 1 penny."
        assert command[-1] == "--stdin"
        path = speech.Path(command[command.index("-w") + 1])
        paths.append(path)
        with wave.open(str(path), "wb") as audio:
            audio.setparams((1, 2, 22050, 0, "NONE", "not compressed"))
            audio.writeframes(b"\x01\x00" * 22050)
    monkeypatch.setattr(speech.subprocess, "run", generate)
    data = speech.synthesise("1 pound and 1 penny.")
    with wave.open(BytesIO(data)) as audio:
        assert audio.getnframes() == 22050
    assert not paths[0].exists()
