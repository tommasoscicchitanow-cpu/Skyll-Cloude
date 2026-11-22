#!/usr/bin/env python3
"""Submit a book to Amazon KDP by driving a logged-in Chrome over CDP.

This encodes the production-tested workarounds for KDP's React form (see
references/kdp-automation.md):
  * attach to an existing, logged-in Chrome (reuses session / 2FA),
  * set field values with JS `evaluate` + input/change events (not Playwright .fill/.type),
  * upload interior/cover via CDP `DOM.setFileInputFiles` (not Playwright set_input_files),
  * select the mandatory AI-content disclosure,
  * stop at review unless --publish is passed.

Setup (once):
  google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/kdp-chrome
  # log into kdp.amazon.com in that window

Run:
  python kdp_upload.py --cdp http://localhost:9222 --metadata book.yaml \
      --interior interior.pdf --cover cover.pdf --format paperback

IMPORTANT: KDP changes selectors over time. The SELECTORS map below is configuration —
re-inspect the live DOM and update it (and references/kdp-automation.md) when a step breaks.
This script is intentionally conservative: it fills, uploads, and pauses for human review.
"""
from __future__ import annotations

import argparse
import asyncio
import os

import yaml

# --- Selector / element-ID configuration (UPDATE when KDP changes) -----------------
SELECTORS = {
    "title": "#data-print-book-title",
    "subtitle": "#data-print-book-subtitle",
    "author_first": "#data-print-book-primary-author-first-name",
    "author_last": "#data-print-book-primary-author-last-name",
    "description": "#data-print-book-description",
    "keyword_slots": [f"#data-print-book-keywords-{i}" for i in range(7)],
    # AI content disclosure
    "ai_yes": "input[name='ai-content'][value='yes']",
    "ai_text": "#ai-content-text",
    "ai_images": "#ai-content-images",
    "ai_translation": "#ai-content-translation",
    # File inputs (hidden, custom uploaders)
    "interior_file": "input[type='file'][data-testid='manuscript-upload']",
    "cover_file": "input[type='file'][data-testid='cover-upload']",
    # Navigation
    "save_continue": "#save-and-continue-announce",
    "publish": "#announce-publish-button",
}

# React-safe value setter (see references/kdp-automation.md, workaround #2).
JS_SET_VALUE = r"""
([selector, value]) => {
  const el = document.querySelector(selector);
  if (!el) return false;
  const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement : HTMLInputElement;
  const setter = Object.getOwnPropertyDescriptor(proto.prototype, 'value').set;
  setter.call(el, value);
  el.dispatchEvent(new Event('input',  { bubbles: true }));
  el.dispatchEvent(new Event('change', { bubbles: true }));
  el.blur();
  return true;
}
"""


def load_metadata(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


async def set_value(page, selector: str, value: str) -> None:
    ok = await page.evaluate(JS_SET_VALUE, [selector, value])
    if not ok:
        print(f"  ! selector not found (skipped): {selector}")
    else:
        print(f"  set {selector}")


async def cdp_upload(page, selector: str, file_path: str) -> None:
    """Upload a file into a hidden input via CDP DOM.setFileInputFiles (workaround #3)."""
    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(abs_path)
    client = await page.context.new_cdp_session(page)
    doc = await client.send("DOM.getDocument", {"depth": -1})
    node = await client.send("DOM.querySelector",
                             {"nodeId": doc["root"]["nodeId"], "selector": selector})
    if not node.get("nodeId"):
        raise RuntimeError(f"file input not found: {selector}")
    await client.send("DOM.setFileInputFiles", {"files": [abs_path], "nodeId": node["nodeId"]})
    print(f"  uploaded {os.path.basename(abs_path)} -> {selector}")


async def fill_metadata(page, md: dict) -> None:
    print("[metadata]")
    if md.get("title"):
        await set_value(page, SELECTORS["title"], md["title"])
    if md.get("subtitle"):
        await set_value(page, SELECTORS["subtitle"], md["subtitle"])
    author = md.get("author", "")
    if author:
        first, _, last = author.partition(" ")
        await set_value(page, SELECTORS["author_first"], first)
        await set_value(page, SELECTORS["author_last"], last or first)
    if md.get("description"):
        await set_value(page, SELECTORS["description"], md["description"])
    for sel, kw in zip(SELECTORS["keyword_slots"], md.get("keywords", [])[:7]):
        await set_value(page, sel, kw)


async def set_ai_disclosure(page, md: dict) -> None:
    """Select the mandatory AI-content disclosure (workaround #4)."""
    ai = md.get("ai_content", {})
    if not ai:
        print("[ai] no ai_content block in metadata; LEAVING DISCLOSURE FOR MANUAL REVIEW")
        return
    print("[ai] selecting AI-content disclosure")
    try:
        await page.click(SELECTORS["ai_yes"])
        for key, sel in (("text", "ai_text"), ("images", "ai_images"),
                         ("translation", "ai_translation")):
            if ai.get(key):
                await page.check(SELECTORS[sel])
    except Exception as exc:  # noqa: BLE001 - surface and let human finish
        print(f"  ! AI disclosure needs manual completion: {exc}")


async def run(args) -> None:
    from playwright.async_api import async_playwright

    md = load_metadata(args.metadata)
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(args.cdp)
        ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()

        print(f"[kdp] using open page: {page.url or '(blank)'}")
        print("[kdp] make sure you are on the KDP 'Create' details step for your "
              f"{args.format}. Reload it if the form looks stale (workaround #2).")

        await fill_metadata(page, md)
        await set_ai_disclosure(page, md)

        if args.interior:
            print("[upload] interior")
            await cdp_upload(page, SELECTORS["interior_file"], args.interior)
        if args.cover:
            print("[upload] cover")
            await cdp_upload(page, SELECTORS["cover_file"], args.cover)

        print("\n[done] Fields filled and files dispatched.")
        print("       Verify uploads finished processing, then review the live preview.")
        if args.publish:
            print("[publish] --publish set: clicking publish after your confirmation.")
            input("       Press Enter to confirm PUBLISH, or Ctrl-C to abort... ")
            await page.click(SELECTORS["publish"])
            print("[publish] submitted.")
        else:
            print("       Stopped at review (no --publish). Nothing was published.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Submit a book to KDP over CDP.")
    ap.add_argument("--cdp", default="http://localhost:9222", help="Chrome CDP endpoint")
    ap.add_argument("--metadata", required=True, help="YAML metadata (title, keywords, ai_content...)")
    ap.add_argument("--interior", help="interior PDF path")
    ap.add_argument("--cover", help="cover PDF path")
    ap.add_argument("--format", default="paperback",
                    choices=["paperback", "hardcover", "ebook"])
    ap.add_argument("--publish", action="store_true",
                    help="actually click Publish after a manual confirm (default: stop at review)")
    args = ap.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
