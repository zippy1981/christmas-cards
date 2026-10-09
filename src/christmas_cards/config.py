"""Settings and secrets, loaded with Dynaconf (see ADR 0011).

Settings are read, in order, from ``settings.toml`` and the git-ignored ``.secrets.toml``
in the working directory, then from ``DYNACONF_*`` environment variables.
"""

from functools import cache
from pathlib import Path
from typing import Any

from dynaconf import Dynaconf


@cache
def get_settings() -> Any:
    """Return the project settings, loading them on first use."""
    return Dynaconf(
        envvar_prefix="DYNACONF",
        # Absolute paths, so Dynaconf doesn't search the script's or package's directories.
        settings_files=[Path.cwd() / "settings.toml", Path.cwd() / ".secrets.toml"],
    )
