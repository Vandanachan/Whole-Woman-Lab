import sys
from pathlib import Path

# make the engine1/ package importable when running pytest from anywhere
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
