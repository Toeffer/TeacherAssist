import sys
from pathlib import Path

# Ensure the repo root is on sys.path so `import tool_server` works
sys.path.insert(0, str(Path(__file__).parent))
