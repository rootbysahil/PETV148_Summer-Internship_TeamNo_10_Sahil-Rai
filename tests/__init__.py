# Unit Tests Suite Configuration for pytest
import sys
from pathlib import Path

# Add current workspace to path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))
