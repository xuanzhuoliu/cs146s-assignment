import sys
from pathlib import Path

# Tests import `week2.github_mcp.*`, so the repo root has to be importable
# regardless of which directory pytest was invoked from.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
