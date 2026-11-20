"""Offline speech from verified summary values; no bank data or network calls."""
from datetime import date
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import wave


def spoken_gbp(pence):
    if not isinstance(pence, int) or isinstance(pence, bool) or pence < 0:
        raise ValueError("Speech amounts must be nonnegative integer pence.")
    pounds, pennies = divmod(pence, 100)
    parts = []
    if pounds or not pennies:
        parts.append(f"{pounds} {'pound' if pounds == 1 else 'pounds'}")
    if pennies:
        parts.append(f"{pennies} {'penny' if pennies == 1 else 'pence'}")
    return " and ".join(parts)


def announcement(summary):
    """Use only calculated fields, never transaction descriptions or free text."""
    count = summary["transaction_count"]
    if not count:
        return "There are no outgoing transactions to summarise."
    dates = [date.fromisoformat(summary[key]) for key in ("start_date", "end_date")]
    start, end = [f"{value.day} {value.strftime('%B %Y')}" for value in dates]
    text = (f"Your fictional transaction file contains {count} outgoing "
            f"{'payment' if count == 1 else 'payments'}, from {start} to {end}, "
            f"totalling {spoken_gbp(summary['total_pence'])}.")
    known = {key: value for key, value in summary["by_category_pence"].items()
             if key in {"groceries", "transport", "shopping", "bills", "entertainment"}}
    if known:
        largest = max(known, key=known.get)
        text += (f" The largest predicted spending category is {largest}, "
                 f"at {spoken_gbp(known[largest])}.")
    review = summary["needs_review"]
    if review:
        text += f" {review} {'transaction needs' if review == 1 else 'transactions need'} a category review."
    return text + " Categories are model estimates. Totals are calculated from the CSV."


def speech_engine():
    if sys.platform == "darwin" and (executable := shutil.which("say")):
        return "macOS system voice", executable
    for name in ("espeak-ng", "espeak"):
        if executable := shutil.which(name):
            return "eSpeak", executable
    return None


def synthesise(text):
    """Create a PCM WAV without playing it; playback needs a separate user action."""
    if not text.strip() or len(text) > 4000:
        raise ValueError("Use a nonempty summary of at most 4,000 characters.")
    engine = speech_engine()
    if engine is None:
        raise RuntimeError("No offline speech engine found. Use macOS with a system voice, or install espeak-ng on Linux.")
    name, executable = engine
    with tempfile.TemporaryDirectory(prefix="studentbank-speech-") as directory:
        output = Path(directory) / "summary.wav"
        if name == "macOS system voice":
            command = [executable, "-o", str(output), "--file-format=WAVE", "--data-format=LEI16@22050", "-r", "165"]
        else:
            command = [executable, "-v", "en-gb", "-s", "165", "-w", str(output), "--stdin"]
        try:
            subprocess.run(command, input=text, text=True, capture_output=True, check=True, timeout=60)
            with wave.open(str(output), "rb") as audio:
                if audio.getnframes() == 0 or audio.getcomptype() != "NONE":
                    raise ValueError("Speech engine returned empty or unsupported audio.")
            return output.read_bytes()
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Speech generation timed out. Try again.") from exc
        except (subprocess.CalledProcessError, OSError, EOFError, wave.Error, ValueError) as exc:
            raise RuntimeError("The offline voice could not create a WAV file. Check that a system voice is installed and try again.") from exc
