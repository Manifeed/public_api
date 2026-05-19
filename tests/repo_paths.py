from __future__ import annotations

import os
from pathlib import Path


def repo_root() -> Path:
	env = os.environ.get("MANIFEED_REPO_ROOT", "").strip()
	if env:
		return Path(env)
	return Path(__file__).resolve().parents[2]


def public_api_root() -> Path:
	return Path(__file__).resolve().parents[1]
