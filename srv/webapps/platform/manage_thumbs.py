# /srv/webapps/platform/manage_thumbs.py

import argparse
import asyncio
import json
import hashlib
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright

BASE_DIR = Path("/srv/webapps")
CLIENTS_DIR = BASE_DIR / "clients"


def hash_target(target: str) -> str:
    """Stable short filename for a given target URL/path."""
    return hashlib.sha1(target.encode("utf-8")).hexdigest()[:16]


def get_client_paths(client_name: str):
    """
    Given a client name (e.g. 'fruitfulnetworkdevelopment.com'),
    return paths we need for thumbnail generation.
    """
    client_root = CLIENTS_DIR / client_name / "frontend"
    data_path = client_root / "user_data.json"
    thumbs_dir = client_root / "assets" / "anthology"
    thumbs_dir.mkdir(parents=True, exist_ok=True)
    return client_root, data_path, thumbs_dir


def to_absolute_url(client: str, target: str) -> str:
    """
    Turn a target into an absolute URL.

    - If target already has a scheme (http/https), return as-is.
    - If target is relative (e.g. '/demo-design-1'), prepend 'https://{client}'.
    """
    parsed = urlparse(target)
    if parsed.scheme:
        return target
    # treat target as a path on this client's domain
    return f"https://{client}{target}"


async def capture_url(page, url: str, out_path: Path):
    await page.set_viewport_size({"width": 1280, "height": 720})
    await page.goto(url, wait_until="networkidle", timeout=30000)
    await page.screenshot(path=str(out_path), full_page=True)


async def capture_pdf(page, pdf_path: Path, out_path: Path):
    html = f"""
    <html><body style="margin:0">
    <embed src="file://{pdf_path}" type="application/pdf" width="100%" height="100%">
    </body></html>
    """
    await page.set_viewport_size({"width": 1280, "height": 720})
    await page.set_content(html)
    await page.screenshot(path=str(out_path), full_page=True)


async def process_client(client: str):
    client_root, data_path, thumbs_dir = get_client_paths(client)

    if not data_path.exists():
        print(f"[{client}] No user_data.json found at {data_path}")
        return

    with data_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Adjust for MSS wrapper: MSS.dossier.anthology.blocks
    mss = data.get("MSS", {})
    dossier = mss.get("dossier", {})
    anthology = dossier.get("anthology", {})
    blocks = anthology.get("blocks", [])

    if not isinstance(blocks, list):
        print(f"[{client}] No blocks[] list found under MSS.dossier.anthology.blocks")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for block in blocks:
            if not isinstance(block, dict):
                # skip any placeholder strings, e.g. "..."
                continue

            # skip already-thumbnailed blocks (static PNGs, etc.)
            if block.get("thumbnail"):
                continue

            kind = block.get("kind")
            target = block.get("target")
            if not kind or not target:
                continue

            print(f"[{client}] Generating thumb for {kind}: {target}")

            filename = hash_target(target) + ".png"
            out_path = thumbs_dir / filename
            web_path = f"assets/anthology/{filename}"

            try:
                if kind == "url":
                    url = to_absolute_url(client, target)
                    await capture_url(page, url, out_path)
                elif kind == "pdf":
                    pdf_fs_path = client_root / target
                    await capture_pdf(page, pdf_fs_path, out_path)
                else:
                    # e.g. "image" or other custom kinds → skip
                    print(f"  - skipping unknown kind={kind}")
                    continue

                block["thumbnail"] = web_path
            except Exception as e:
                print(f"  ! Error generating thumbnail for {target}: {e}")

        await browser.close()

    # Write updated data (with thumbnails) back into user_data.json
    with data_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"[{client}] Updated {data_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--client",
        required=True,
        help="Client folder name under /srv/webapps/clients "
             "(e.g. fruitfulnetworkdevelopment.com)",
    )
    args = parser.parse_args()
    asyncio.run(process_client(args.client))


if __name__ == "__main__":
    main()
