# scraper.py
import argparse
import os
import re
import json
from urllib.parse import urlparse, urljoin
from urllib import robotparser

import requests
from bs4 import BeautifulSoup

from utils import (
    slugify,
    canonical_url,
    in_same_domain,
    respectful_sleep,
    save_text,
    append_jsonl,
)

HEADERS = {
    "User-Agent": "SDG-AI-Lab-ResearchBot/1.0 (+contact: research@example.org)"
}


def can_fetch(url: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch("*", url)
    except Exception:
        # Eğer robots.txt okunamazsa temkinli ama izin ver
        return True


def get(url: str, timeout: int = 20):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        return r
    except Exception:
        return None


def visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # script/style gibi gürültüleri temizle
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)
    # çoklu yeni satırları sadeleştir
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def load_patterns(patterns_path: str):
    with open(patterns_path, "r", encoding="utf-8") as f:
        patt = json.load(f)
    page_kw = [re.escape(k) for k in patt.get("page_keywords", [])]
    pdf_kw = [re.escape(k) for k in patt.get("pdf_keywords", [])]
    return re.compile("|".join(page_kw), re.IGNORECASE), re.compile("|".join(pdf_kw), re.IGNORECASE)


def should_keep_page(url: str, text: str, page_regex) -> bool:
    return bool(page_regex.search(url)) or bool(page_regex.search(text[:4000]))


def should_download_pdf(url: str, link_text: str, pdf_regex) -> bool:
    candidate = f"{url} {link_text or ''}"
    return bool(pdf_regex.search(candidate))


def crawl(
    org: str,
    seed: str,
    outdir: str,
    max_pages: int,
    max_depth: int,
    delay: float,
    patterns_path: str,
    max_pdf_mb: int = 80,
):
    org_slug = slugify(org)
    org_dir = os.path.join(outdir, org_slug)
    html_dir = os.path.join(org_dir, "html")
    pdf_dir = os.path.join(org_dir, "pdfs")
    log_path = os.path.join(org_dir, "meta.jsonl")
    os.makedirs(html_dir, exist_ok=True)
    os.makedirs(pdf_dir, exist_ok=True)

    page_regex, pdf_regex = load_patterns(patterns_path)

    # seed normalize
    if not seed.startswith("http"):
        seed = "https://" + seed.strip("/")
    seed = canonical_url(seed)

    if not can_fetch(seed):
        append_jsonl(log_path, {"org": org, "event": "blocked_by_robots", "url": seed})
        return

    queue = [(seed, 0)]
    seen = set()

    while queue and len(seen) < max_pages:
        url, depth = queue.pop(0)
        url = canonical_url(url)

        if url in seen or depth > max_depth:
            continue
        if not in_same_domain(seed, url):
            continue
        if not can_fetch(url):
            append_jsonl(log_path, {"org": org, "event": "disallowed", "url": url})
            continue

        seen.add(url)
        respectful_sleep(delay)

        resp = get(url)
        if not resp or resp.status_code >= 400:
            append_jsonl(
                log_path,
                {
                    "org": org,
                    "event": "error",
                    "url": url,
                    "status": getattr(resp, "status_code", None),
                },
            )
            continue

        ctype = (resp.headers.get("Content-Type") or "").lower()
        if "pdf" in ctype or url.lower().endswith(".pdf"):
            # PDF'leri linkler üzerinden ele alacağız; sayfa kuyruğunu kirletmeyelim
            continue

        html = resp.text or ""
        text = visible_text(html)

        # İlgili sayfayı kaydet
        if should_keep_page(url, text, page_regex):
            fname = re.sub(r"[^a-zA-Z0-9]+", "_", urlparse(url).path.strip("/") or "index")[:80]
            html_path = os.path.join(html_dir, f"{fname}.html")
            txt_path = os.path.join(html_dir, f"{fname}.txt")
            save_text(html_path, html)
            save_text(txt_path, text)
            append_jsonl(
                log_path,
                {"org": org, "event": "save_page", "url": url, "html": html_path, "txt": txt_path},
            )

        # Linkleri tara
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            target = urljoin(url, href)

            # Dahili linkleri kuyruğa ekle
            if in_same_domain(seed, target):
                if (target not in seen) and (len(seen) + len(queue) < max_pages):
                    queue.append((target, depth + 1))

            # PDF indir
            if target.lower().endswith(".pdf"):
                link_text = (a.get_text(strip=True) or "")[:120]
                if should_download_pdf(target, link_text, pdf_regex):
                    if can_fetch(target):
                        try:
                            r = requests.get(target, headers=HEADERS, timeout=30, stream=True)
                            r.raise_for_status()
                            total = 0
                            max_bytes = max_pdf_mb * 1024 * 1024
                            pdf_name = re.sub(
                                r"[^a-zA-Z0-9]+", "_", os.path.basename(urlparse(target).path)
                            )[:90] or "file.pdf"
                            pdf_path = os.path.join(pdf_dir, pdf_name)
                            with open(pdf_path, "wb") as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    if not chunk:
                                        break
                                    total += len(chunk)
                                    if total > max_bytes:
                                        append_jsonl(
                                            log_path,
                                            {
                                                "org": org,
                                                "event": "pdf_too_large",
                                                "url": target,
                                                "size_bytes": total,
                                            },
                                        )
                                        break
                                    f.write(chunk)
                            if total <= max_bytes and total > 0:
                                append_jsonl(
                                    log_path,
                                    {
                                        "org": org,
                                        "event": "save_pdf",
                                        "url": target,
                                        "pdf": pdf_path,
                                        "link_text": link_text,
                                    },
                                )
                        except Exception as e:
                            append_jsonl(
                                log_path,
                                {"org": org, "event": "pdf_error", "url": target, "error": str(e)},
                            )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--org", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max_pages", type=int, default=40)
    ap.add_argument("--max_depth", type=int, default=2)
    ap.add_argument("--delay", type=float, default=1.5)
    ap.add_argument("--patterns", default="patterns.json")
    args = ap.parse_args()
    crawl(
        args.org,
        args.url,
        args.out,
        args.max_pages,
        args.max_depth,
        args.delay,
        args.patterns,
    )