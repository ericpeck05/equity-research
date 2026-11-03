"""Settings for the toolkit.

The SEC requires every automated request to identify who is making it
("Your Name your@email.com"). Set it once in config.toml (copy
config.example.toml) or in the SEC_USER_AGENT environment variable.
"""
from __future__ import annotations

import os
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
COVERAGE_DIR = ROOT / "coverage"
CONFIG_FILE = ROOT / "config.toml"


def _load() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "rb") as f:
            return tomllib.load(f)
    return {}


def sec_user_agent() -> str:
    ua = os.environ.get("SEC_USER_AGENT") or _load().get("sec_user_agent", "")
    if not ua or "@" not in ua:
        raise SystemExit(
            "SEC needs a contact in every request.\n"
            "Copy config.example.toml to config.toml and set sec_user_agent = "
            '"Your Name your@email.com" (or set the SEC_USER_AGENT variable).'
        )
    return ua


def cache_max_age_hours() -> float:
    return float(_load().get("cache_max_age_hours", 12))
