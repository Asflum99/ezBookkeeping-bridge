import sys
from pathlib import Path

# Add src to path so imports work like they do in the app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
