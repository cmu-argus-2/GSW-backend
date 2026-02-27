import sys
import os
from pathlib import Path


def _load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")

        # Do not override vars already provided by the shell environment.
        if key and key not in os.environ:
            os.environ[key] = value


_load_env_file(Path(__file__).resolve().parent / ".env")

from lib.shell_utils import op_mode


while True:
    connection_prompt = """
What operation mode do you want?
(o) Operations Mode 
(q) quit   
Input: """
    conn_type = input(connection_prompt)
    if conn_type == "q":
        sys.exit(0)

    options = {
        "o": op_mode
    }

    options[conn_type]()
