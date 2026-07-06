import sys
from pathlib import Path

# Insert parent directory to system path for running CLI directly
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from src.cli import app

if __name__ == "__main__":
    app()
