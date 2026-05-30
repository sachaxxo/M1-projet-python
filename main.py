"""Point d'entrée : lance la CLI sans installation du package."""

from __future__ import annotations

import sys
from pathlib import Path

# Permet d'importer depuis src/ sans installer le package
sys.path.append(str(Path(__file__).parent / "src"))

from consulting_scheduler.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
