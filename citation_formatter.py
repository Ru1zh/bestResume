"""Render structured resume publications as safe HTML."""

from __future__ import annotations

import html
import re
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse


SUPPORTED_STYLES = {"ieee", "apa", "mla"}


def _escape(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _safe_url(value: Any) -> str:
    url = str(value or "").strip()
    parsed = urlparse(url)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return url
    return ""


def _doi_url(value: Any) -> str:
    doi = str(value or "").strip()
    if not doi:
        return ""
    if doi.startswith("http://") or doi.startswith("https://"):
        return _safe_url(doi)
    return "https://doi.org/" + doi.removeprefix("doi:").strip()


def _link(url: str) -> str:
    safe = _safe_url(url)
    if not safe:
        return ""
    escaped = _escape(safe)
    return f'<a href="{escaped}" target="_blank" rel="noreferrer">{escaped}</a>'


def _author_text(author: Any) -> str:
    if isinstance(author, dict):
        given = str(author.get("given", "")).strip()
        family = str(author.get("family", "")).strip()
        return " ".join(part for part in (given, family) if part)
    return str(author or "").strip()


def _authors(value: Any, style: str) -> str:
    if isinstance(value, str):
        names = [value.strip()] if value.strip() else []
    elif isinstance(value, list):
        names = [_author_text(item) for item in value if _author_text(item)]
    else:
        names = []

    escaped = [_escape(name) for name in names]
    if not escaped:
        return ""
    if style == "apa":
        return ", ".join(escaped[:-1]) + (f", &amp; {escaped[-1]}" if len(escaped) > 1 else escaped[0])
    if style == "mla":
        return ", ".join(escaped[:-1]) + (f", and {escaped[-1]}" if len(escaped) > 1 else escaped[0])
    return ", ".join(escaped[:-1]) + (f", and {escaped[-1]}" if len(escaped) > 1 else escaped[0])


def _value(item: Dict[str, Any], key: str) -> str:
    return str(item.get(key, "") or "").strip()


def _title(item: Dict[str, Any]) -> str:
    return _value(item, "title").rstrip(".,;。； ")


def _container(item: Dict[str, Any]) -> str:
    return _value(item, "container_title").rstrip(".,;。； ")


def _doi_or_url(item: Dict[str, Any]) -> str:
    return _doi_url(item.get("doi")) or _safe_url(item.get("url"))


def _legacy_html(item: Dict[str, Any]) -> str:
    text = _escape(item.get("text", "").strip())
    url = _safe_url(item.get("url"))
    return text + (f" <em>{_escape(item.get('container_title'))}</em>" if item.get("container_title") else "") + (f" {_link(url)}." if url else "")


def _ieee(item: Dict[str, Any], number: int) -> str:
    authors = _authors(item.get("authors"), "ieee")
    title = _title(item)
    container = _container(item)
    parts: List[str] = []
    if authors:
        parts.append(authors + (", " if title else ". "))
    if title:
        parts.append(f'"{_escape(title)},"')
    if container:
        parts.append(f" in <em>{_escape(container)}</em>" if _value(item, "type").lower() == "conference" else f", <em>{_escape(container)}</em>")
    volume = _value(item, "volume")
    issue = _value(item, "issue")
    pages = _value(item, "pages")
    if volume:
        parts.append(f", vol. {_escape(volume)}")
    if issue:
        parts.append(f", no. {_escape(issue)}")
    if pages:
        prefix = "p." if _value(item, "type").lower() == "conference" else "pp."
        parts.append(f", {prefix} {_escape(pages)}")
    year = _value(item, "year")
    if year:
        parts.append(f", {_escape(year)}")
    result = "".join(parts).strip()
    link = _link(_doi_or_url(item))
    return f"[{number}] " + result + (f". doi: {link}" if link else ".")


def _apa(item: Dict[str, Any]) -> str:
    authors = _authors(item.get("authors"), "apa")
    year = _value(item, "year")
    title = _title(item)
    container = _container(item)
    result = f"{authors} ({_escape(year)}). " if authors and year else (f"{authors}. " if authors else "")
    if title:
        result += _escape(title) + ". "
    if container:
        result += f"<em>{_escape(container)}</em>"
    volume = _value(item, "volume")
    issue = _value(item, "issue")
    pages = _value(item, "pages")
    if volume:
        result += f", {_escape(volume)}"
        if issue:
            result += f"({_escape(issue)})"
    if pages:
        result += f", {_escape(pages)}"
    result = result.rstrip() + "."
    link = _link(_doi_or_url(item))
    return result + (f" {link}" if link else "")


def _mla(item: Dict[str, Any]) -> str:
    authors = _authors(item.get("authors"), "mla")
    title = _title(item)
    container = _container(item)
    result = f"{authors}. " if authors else ""
    if title:
        result += f'"{_escape(title)}." '
    if container:
        result += f"<em>{_escape(container)}</em>"
    volume = _value(item, "volume")
    issue = _value(item, "issue")
    year = _value(item, "year")
    pages = _value(item, "pages")
    if volume:
        result += f", vol. {_escape(volume)}"
    if issue:
        result += f", no. {_escape(issue)}"
    if year:
        result += f", {_escape(year)}"
    if pages:
        result += f", pp. {_escape(pages)}"
    result = result.rstrip(" ,") + "."
    link = _link(_doi_or_url(item))
    return result + (f" {link}" if link else "")


def prepare_publications(
    publications: Iterable[Any],
    default_style: str = "ieee",
) -> List[Dict[str, Any]]:
    """Format structured publications and omit entries without usable content."""

    default = default_style.lower().strip() if isinstance(default_style, str) else "ieee"
    if default not in SUPPORTED_STYLES:
        default = "ieee"

    prepared: List[Dict[str, Any]] = []
    for item in publications or []:
        if not isinstance(item, dict):
            continue
        title = _title(item)
        legacy_text = str(item.get("text", "") or "").strip()
        if not title and not legacy_text:
            continue
        style = str(item.get("style", default) or default).lower().strip()
        if style not in SUPPORTED_STYLES:
            style = default
        if title:
            if style == "ieee":
                rendered = _ieee(item, len(prepared) + 1)
            else:
                renderer = {"apa": _apa, "mla": _mla}[style]
                rendered = renderer(item)
        else:
            rendered = _legacy_html(item)
        prepared.append({"html": rendered, "style": style})
    return prepared
