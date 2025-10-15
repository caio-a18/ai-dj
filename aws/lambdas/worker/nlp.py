from __future__ import annotations

import re
from typing import Tuple

# Naive parse: extract quoted song if present; fallback to whole prompt; count default=20.
def extract_base_query(prompt: str) -> Tuple[str, int]:
    """Naive parse: extract quoted song if present; fallback to whole prompt; count default=20.
    e.g., "generate me a playlist of 20 songs like 'Blinding Lights'" -> ("Blinding Lights", 20)
    """
    m = re.search(r"(\d+)\s+songs?", prompt, re.IGNORECASE)
    count = int(m.group(1)) if m else 20
    qmatch = re.search(r"'([^']+)'|\"([^\"]+)\"", prompt)
    if qmatch:
        base = qmatch.group(1) or qmatch.group(2)
    else:
        # fallback to last few words
        parts = re.findall(r"[\w\s]+", prompt)
        base = prompt if not parts else " ".join(prompt.split()[-5:])
    return base.strip(), count

# Simple enhancement hook (can be upgraded later)
def enhance_query(prompt: str) -> Tuple[str, int]:
    return extract_base_query(prompt)
