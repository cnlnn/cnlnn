#!/usr/bin/env python3

from __future__ import annotations

import os
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

FEED_URL = os.environ.get("BLOG_FEED_URL", "https://cnlnn.pages.dev/atom.xml")
README_PATH = Path(os.environ.get("PROFILE_README", "README.md"))
MAX_POSTS = 5
START_MARKER = "<!-- BLOG-POST-LIST:START -->"
END_MARKER = "<!-- BLOG-POST-LIST:END -->"
ATOM = {"atom": "http://www.w3.org/2005/Atom"}


def markdown_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def fetch_posts() -> list[tuple[str, str, str]]:
    request = urllib.request.Request(
        FEED_URL,
        headers={"User-Agent": "cnlnn-profile-readme/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        root = ET.fromstring(response.read())

    posts: list[tuple[str, str, str]] = []
    for entry in root.findall("atom:entry", ATOM):
        title = (entry.findtext("atom:title", default="", namespaces=ATOM)).strip()
        published = entry.findtext("atom:published", default="", namespaces=ATOM)
        link = next(
            (
                element.get("href", "")
                for element in entry.findall("atom:link", ATOM)
                if element.get("rel", "alternate") == "alternate"
            ),
            "",
        )
        if not link:
            link_element = entry.find("atom:link", ATOM)
            link = link_element.get("href", "") if link_element is not None else ""
        if title and link:
            posts.append((title, link, published[:10]))
        if len(posts) == MAX_POSTS:
            break

    if not posts:
        raise RuntimeError("The Atom feed did not contain any usable posts")
    return posts


def update_readme(posts: list[tuple[str, str, str]]) -> None:
    source = README_PATH.read_text(encoding="utf-8")
    if source.count(START_MARKER) != 1 or source.count(END_MARKER) != 1:
        raise RuntimeError("README blog post markers are missing or duplicated")

    lines = []
    for title, url, published in posts:
        date = f" <sub>{published}</sub>" if published else ""
        lines.append(f"- [{markdown_escape(title)}]({url}){date}")

    before, remainder = source.split(START_MARKER, 1)
    _, after = remainder.split(END_MARKER, 1)
    updated = before + START_MARKER + "\n" + "\n".join(lines) + "\n" + END_MARKER + after
    README_PATH.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    update_readme(fetch_posts())

