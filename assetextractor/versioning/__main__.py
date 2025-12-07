"""
Module entry point for asset versioning system.

Allows running the versioning system as:
    python -m assetextractor.versioning [command] [options]
"""

import sys

from assetextractor.versioning.cli import main

if __name__ == "__main__":
    sys.exit(main())
