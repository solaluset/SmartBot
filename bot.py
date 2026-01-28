import os
import sys
import subprocess

while True:
    try:
        if subprocess.call(
            [sys.executable, "_bot.py"] + sys.argv[1:]
        ) == 0 and not os.path.isfile("restart"):
            break
    except KeyboardInterrupt:
        break
