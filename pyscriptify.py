"""
Make tutorials with dependencies from ../bundle/ address
https://webgl.langa.pl/bundle/ instead, making them work from Pyscript.com.
"""

from pathlib import Path
import re

CURRENT_DIR = Path(__file__).parent
BUNDLE_RE = re.compile(rb"""(['"])(\.\./bundle/)""")

for path in CURRENT_DIR.glob("tutorial[123456789]/**"):
    if path.is_file():
        data = path.read_bytes()
        data_new = BUNDLE_RE.sub(rb"\1https://webgl.langa.pl/bundle/", data)
        if data != data_new:
            print(path)
            path.write_bytes(data_new)
