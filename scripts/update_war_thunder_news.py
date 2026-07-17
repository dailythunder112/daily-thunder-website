#!/usr/bin/env python3
"""Fetch the latest official War Thunder news and changelog entries."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


BASE_URL = "https://warthunder.com"
NEWS_URL = f"{BASE_URL}/en/news"
CHANGELOG_URL = f"{BASE_URL}/en/game/changelog/page/1"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
OUTPUT_PATH = DATA_DIR / "war-thunder-news.json"
JS_OUTPUT_PATH = DATA_DIR / "war-thunder-news.js"
USER_AGENT = "DailyThunderNewsBot/1.0 (+https://warthunder.com/en/news)"
MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}


@dataclass
class Entry:
    title: str = ""
    summary: str = ""
    date_text: str = ""
    url: str = ""
    kind: str = "news"


class ShowcaseParser(HTMLParser):
    VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, kind: str) -> None:
        super().__init__(convert_charrefs=True)
        self.kind = kind
        self.entries: list[Entry] = []
        self.card: Entry | None = None
        self.card_depth = 0
        self.capture: str | None = None
        self.capture_depth = 0
        self.buffer: list[str] = []

    @staticmethod
    def _classes(attrs: list[tuple[str, str | None]]) -> set[str]:
        value = dict(attrs).get("class") or ""
        return set(value.split())

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = self._classes(attrs)
        values = dict(attrs)

        if tag == "div" and {"showcase__item", "widget"}.issubset(classes):
            if self.card is not None:
                self._finish_card()
            self.card = Entry(kind=self.kind)
            self.card_depth = 1
            return

        if self.card is None:
            return

        if tag not in self.VOID_TAGS:
            self.card_depth += 1
        if tag == "a" and "widget__link" in classes and not self.card.url:
            self.card.url = urljoin(BASE_URL, values.get("href") or "")
        if "widget__title" in classes:
            self._start_capture("title")
        elif "widget__comment" in classes:
            self._start_capture("summary")
        elif "widget-meta__item--right" in classes:
            self._start_capture("date_text")
        elif self.capture:
            self.capture_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self.card is None:
            return

        if self.capture:
            self.capture_depth -= 1
            if self.capture_depth == 0:
                value = clean_text(" ".join(self.buffer))
                setattr(self.card, self.capture, value)
                self.capture = None
                self.buffer = []

        self.card_depth -= 1
        if self.card_depth == 0:
            self._finish_card()

    def handle_data(self, data: str) -> None:
        if self.capture:
            self.buffer.append(data)

    def _start_capture(self, field: str) -> None:
        self.capture = field
        self.capture_depth = 1
        self.buffer = []

    def _finish_card(self) -> None:
        if self.card and self.card.title and self.card.url and self.card.date_text:
            self.entries.append(self.card)
        self.card = None
        self.card_depth = 0
        self.capture = None
        self.capture_depth = 0
        self.buffer = []

    def finish(self) -> None:
        if self.card is not None:
            self._finish_card()


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def fetch(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "en"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_page(url: str, kind: str) -> list[Entry]:
    parser = ShowcaseParser(kind)
    parser.feed(fetch(url))
    parser.close()
    parser.finish()
    return parser.entries


def parse_date(value: str) -> datetime:
    match = re.fullmatch(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", value.strip())
    if not match or match.group(2) not in MONTHS:
        raise ValueError(f"Unsupported date: {value!r}")
    return datetime(int(match.group(3)), MONTHS[match.group(2)], int(match.group(1)))


def category_key(entry: Entry) -> str:
    if entry.kind == "update":
        return "update"
    slug = entry.url.lower()
    mapping = {
        "development": "development", "event": "event", "esports": "esports",
        "shop": "shop", "market": "market", "decals": "decals",
        "fair-play": "fair_play", "special": "special",
    }
    return next((label for key, label in mapping.items() if f"-{key}-" in slug), "news")


def category(entry: Entry) -> str:
    labels = {
        "development": "VÝVOJ", "event": "EVENT", "esports": "ESPORTS",
        "shop": "SHOP", "market": "MARKET", "decals": "DECALS",
        "fair_play": "FAIR PLAY", "special": "SPECIAL", "news": "NOVINKA", "update": "UPDATE",
    }
    return labels[category_key(entry)]


def trim_summary(value: str, limit: int = 210) -> str:
    value = clean_text(value)
    if len(value) <= limit:
        return value
    shortened = value[: limit - 1].rsplit(" ", 1)[0]
    return f"{shortened}…"


def serialize(entries: Iterable[Entry]) -> dict[str, object]:
    try:
        now = datetime.now(ZoneInfo("Europe/Bratislava"))
    except ZoneInfoNotFoundError:
        # Windows installations without the optional tzdata package still
        # expose the computer's configured local timezone through astimezone.
        now = datetime.now().astimezone()
    prepared = []
    seen: set[str] = set()
    for entry in sorted(entries, key=lambda item: parse_date(item.date_text), reverse=True):
        if entry.url in seen:
            continue
        seen.add(entry.url)
        date = parse_date(entry.date_text)
        prepared.append({
            "title": clean_text(entry.title),
            "summary": trim_summary(entry.summary),
            "date": date.strftime("%Y-%m-%d"),
            "date_display": f"{date.day}. {date.month}. {date.year}",
            "category": category(entry),
            "category_key": category_key(entry),
            "url": entry.url,
            "kind": entry.kind,
        })
        if len(prepared) == 6:
            break
    if len(prepared) < 3:
        raise RuntimeError(f"Expected at least 3 entries, received {len(prepared)}")
    return {
        "updated_at": now.isoformat(timespec="seconds"),
        "updated_display": f"{now.day}. {now.month}. {now.year} o {now:%H:%M}",
        "source": NEWS_URL,
        "items": prepared,
    }


def main() -> None:
    entries = parse_page(NEWS_URL, "news") + parse_page(CHANGELOG_URL, "update")
    payload = serialize(entries)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if OUTPUT_PATH.exists():
        try:
            previous = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
            if previous.get("items") == payload.get("items") and JS_OUTPUT_PATH.exists():
                print("No new War Thunder entries. Keeping the existing radar.")
                return
        except (json.JSONDecodeError, OSError):
            pass
    json_text = json.dumps(payload, ensure_ascii=False, indent=2)
    OUTPUT_PATH.write_text(json_text + "\n", encoding="utf-8")
    JS_OUTPUT_PATH.write_text(f"window.DT_NEWS_DATA = {json_text};\n", encoding="utf-8")
    print(f"Updated the JSON and JavaScript radar with {len(payload['items'])} items.")


if __name__ == "__main__":
    main()
