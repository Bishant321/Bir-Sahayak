from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parent.parent
with (ROOT / "config.toml").open("rb") as file:
    CONFIG = tomllib.load(file)
