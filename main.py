"""Legacy entry point - use 'build-mpq' CLI or 'python -m build_mpq.cli' instead."""

import sys

from build_mpq.cli import main

if __name__ == "__main__":
    sys.exit(main())
