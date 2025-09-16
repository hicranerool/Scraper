# utils.py
import re, os, time, json
from urllib.parse import urlparse, urldefrag

def slugify(name: str) -> str:
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "-", name).strip("-")
    return name or "org"

def canonical_url(u: str) -> str:
    u = urldefrag(u)[0]
    if not u.endswith("/") and ("/" not in os.path.basename(u)):
        return u if "." in os.path.basename(u) else u + "/"
    return u

def in_same_domain(seed: str, target: str) -> bool:
    a = urlparse(seed).netloc.lower()
    b = urlparse(target).netloc.lower()
    return a == b or a.endswith("." + b) or b.endswith("." + a)

def respectful_sleep(seconds: float):
    try:
        time.sleep(max(0.1, float(seconds)))
    except Exception:
        time.sleep(1.0)

def save_text(path: str, text: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", errors="ignore") as f:
        f.write(text)

def append_jsonl(path: str, obj: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")