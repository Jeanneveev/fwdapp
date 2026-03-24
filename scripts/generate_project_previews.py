#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def discover_projects(index_path: Path) -> list[dict[str, str]]:
    soup = BeautifulSoup(index_path.read_text(encoding="utf-8"), "html.parser")
    projects: list[dict[str, str]] = []

    for card in soup.select("article.card"):
        title_link = card.select_one("h3 a.project-title-link")
        if not title_link:
            continue

        local_href = (title_link.get("href") or "").strip()
        if not local_href:
            continue

        slug = Path(local_href).parent.name
        if not slug:
            continue

        external_link = None
        for link in card.select("a[href]"):
            href = (link.get("href") or "").strip()
            if href.startswith("http://") or href.startswith("https://"):
                external_link = href
                break

        if external_link:
            projects.append(
                {
                    "slug": slug,
                    "title": title_link.get_text(strip=True),
                    "url": external_link,
                }
            )

    return projects


def is_previewable_href(href: str) -> bool:
    return href.startswith("http://") or href.startswith("https://") or href.endswith(
        ".html"
    )


def capture_url_for_href(href: str, index_path: Path) -> str:
    if href.startswith("http://") or href.startswith("https://"):
        return href
    return (index_path.parent / href).resolve().as_uri()


def discover_link_preview_entries(index_path: Path) -> list[dict[str, str]]:
    soup = BeautifulSoup(index_path.read_text(encoding="utf-8"), "html.parser")
    entries: list[dict[str, str]] = []
    seen_hrefs: set[str] = set()

    for card in soup.select("section.projects-grid article.card"):
        links = []
        for link in card.select("a.btn[href]"):
            href = (link.get("href") or "").strip()
            if not href or not is_previewable_href(href):
                continue
            links.append((href, link.get_text(strip=True)))

        if not links:
            continue

        for href, label in links:
            if href in seen_hrefs:
                continue
            seen_hrefs.add(href)
            digest = hashlib.sha1(href.encode("utf-8")).hexdigest()[:12]
            filename = f"link-{digest}.png"
            entries.append(
                {
                    "href": href,
                    "label": label,
                    "capture_url": capture_url_for_href(href, index_path),
                    "filename": filename,
                }
            )

    return entries


def screenshot_target(
    page, output_path: Path, capture_url: str, label: str, force: bool = False
) -> None:
    if output_path.exists() and not force:
        print(f"[skip] {label}: {output_path} already exists")
        return

    print(f"[capture] {label}: {capture_url}")
    try:
        page.goto(capture_url, wait_until="domcontentloaded", timeout=45000)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
    except Exception as exc:
        fallback_html = f"""
        <!doctype html>
        <html>
          <head>
            <meta charset="utf-8" />
            <style>
              body {{
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                color: #231d33;
                background: linear-gradient(145deg, #fcf9ff, #f1eafe);
                display: grid;
                place-items: center;
                height: 100vh;
                padding: 2rem;
              }}
              .box {{
                width: min(920px, 100%);
                border: 1px solid #cfc1eb;
                border-radius: 14px;
                background: #fff;
                padding: 1.2rem;
              }}
              h1 {{
                margin: 0 0 0.5rem;
                font-size: 1.3rem;
              }}
              p {{
                margin: 0.45rem 0;
                overflow-wrap: anywhere;
              }}
            </style>
          </head>
          <body>
            <div class="box">
              <h1>Preview unavailable: {label}</h1>
              <p><strong>URL:</strong> {capture_url}</p>
              <p><strong>Error:</strong> {exc}</p>
            </div>
          </body>
        </html>
        """
        page.set_content(fallback_html, wait_until="load")

    page.screenshot(path=str(output_path), full_page=False)
    print(f"[saved] {output_path}")


def screenshot_projects(
    projects: list[dict[str, str]], output_dir: Path, force: bool = False
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1366, "height": 900},
            ignore_https_errors=True,
        )
        page = context.new_page()

        for project in projects:
            slug = project["slug"]
            title = project["title"]
            url = project["url"]
            output_path = output_dir / f"{slug}.png"
            screenshot_target(page, output_path, url, title, force=force)

        context.close()
        browser.close()


def screenshot_multi_link_entries(
    entries: list[dict[str, str]],
    output_dir: Path,
    force: bool = False,
) -> dict[str, str]:
    link_preview_dir = output_dir / "link-previews"
    link_preview_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, str] = {}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1366, "height": 900},
            ignore_https_errors=True,
        )
        page = context.new_page()

        for entry in entries:
            href = entry["href"]
            label = entry["label"]
            capture_url = entry["capture_url"]
            filename = entry["filename"]
            output_path = link_preview_dir / filename

            screenshot_target(page, output_path, capture_url, label, force=force)
            manifest[href] = f"images/previews/link-previews/{filename}"

        context.close()
        browser.close()

    return manifest


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent

    parser = argparse.ArgumentParser(
        description="Discover project links from homepage and generate preview screenshots."
    )
    parser.add_argument(
        "--index",
        default="index.html",
        help="Path to homepage index HTML (default: index.html)",
    )
    parser.add_argument(
        "--output-dir",
        default="images/previews",
        help="Directory to write preview images (default: images/previews)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing preview images.",
    )
    args = parser.parse_args()

    raw_index = Path(args.index)
    raw_output = Path(args.output_dir)
    index_path = (
        raw_index.resolve() if raw_index.is_absolute() else (project_root / raw_index).resolve()
    )
    output_dir = (
        raw_output.resolve()
        if raw_output.is_absolute()
        else (project_root / raw_output).resolve()
    )

    projects = discover_projects(index_path)
    if not projects:
        raise SystemExit("No projects discovered. Check homepage structure.")

    print(f"Discovered {len(projects)} project links.")
    screenshot_projects(projects, output_dir, force=args.force)

    link_preview_entries = discover_link_preview_entries(index_path)
    print(f"Discovered {len(link_preview_entries)} link previews.")
    manifest = screenshot_multi_link_entries(
        link_preview_entries, output_dir, force=args.force
    )
    manifest_path = output_dir / "link-preview-manifest.json"
    manifest_path.write_text(
        json.dumps({"by_href": manifest}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"[saved] {manifest_path}")
    print("Done.")


if __name__ == "__main__":
    main()
