#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Classify and fetch arXiv items, public PDFs, project pages, blogs, and local files."""

import argparse
import hashlib
import json
import logging
import os
import re
import sys
from html import unescape
from html.parser import HTMLParser
from itertools import chain
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import requests

logger = logging.getLogger(__name__)

ARXIV_MODERN_RE = re.compile(r"(?<!\d)(\d{4}\.\d{4,5})(v\d+)?(?!\d)", re.IGNORECASE)
ARXIV_OLD_RE = re.compile(r"([a-z-]+(?:\.[A-Z]{2})?/\d{7})(v\d+)?", re.IGNORECASE)
MAX_HTML_BYTES = 12 * 1024 * 1024
MAX_PDF_BYTES = 200 * 1024 * 1024
USER_AGENT = "evil-read-arxiv/3.0 (+public research source resolver)"
MARKDOWN_URL_RE = re.compile(r"\[[^\]]*\]\((https?://[^\s)]+)\)", re.IGNORECASE)
PLAIN_URL_RE = re.compile(r"https?://[^\s<>\[\]()]+", re.IGNORECASE)


def stable_id(prefix, value):
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def extract_source_reference(value):
    """Accept a raw ID/path/URL or a URL pasted as a Markdown link."""
    value = value.strip()
    markdown_urls = MARKDOWN_URL_RE.findall(value)
    if markdown_urls:
        return markdown_urls[-1].rstrip(".,;!?")
    if value.startswith("<") and value.endswith(">"):
        value = value[1:-1].strip()
    plain_urls = PLAIN_URL_RE.findall(value)
    if plain_urls and (len(plain_urls) == 1 or any(char.isspace() for char in value)):
        return plain_urls[-1].rstrip(".,;!?")
    return value


def normalize_arxiv_id(value):
    value = value.strip()
    parsed = urlparse(value)
    explicit_arxiv = value.lower().startswith("arxiv:")

    if parsed.scheme in {"http", "https"}:
        host = (parsed.hostname or "").lower()
        if host not in {"arxiv.org", "www.arxiv.org", "export.arxiv.org"}:
            return None
        candidate = unquote(parsed.path).strip("/")
        candidate = re.sub(r"^(abs|pdf|html|e-print)/", "", candidate, flags=re.IGNORECASE)
        candidate = re.sub(r"\.pdf$", "", candidate, flags=re.IGNORECASE)
    else:
        candidate = re.sub(r"^arxiv:\s*", "", value, flags=re.IGNORECASE).strip()

    modern = ARXIV_MODERN_RE.fullmatch(candidate)
    if modern:
        paper_id = modern.group(1)
        month = int(paper_id[2:4])
        if 1 <= month <= 12:
            version = modern.group(2) or ""
            return paper_id + version.lower()
        return None

    if explicit_arxiv or parsed.scheme in {"http", "https"}:
        old = ARXIV_OLD_RE.fullmatch(candidate)
        if old:
            return old.group(1) + (old.group(2) or "").lower()
    return None


def safe_stem(value, fallback):
    value = unquote(value or "")
    value = re.sub(r"[^\w.-]+", "_", value, flags=re.UNICODE).strip("._")
    return value[:120] or fallback


def parse_content_disposition(value):
    if not value:
        return None
    match = re.search(r"filename\*?=(?:UTF-8''|[\"']?)([^\"';]+)", value, re.IGNORECASE)
    return unquote(match.group(1)).strip() if match else None


def pdf_metadata(path):
    result = {}
    try:
        import fitz

        with fitz.open(path) as doc:
            metadata = doc.metadata or {}
            result["page_count"] = doc.page_count
        if metadata.get("title"):
            result["title"] = metadata["title"].strip()
        if metadata.get("author"):
            result["authors"] = metadata["author"].strip()
        raw_date = metadata.get("creationDate") or metadata.get("modDate") or ""
        match = re.search(r"D:(\d{4})(\d{2})(\d{2})", raw_date)
        if match:
            result["published_date"] = "-".join(match.groups())
    except Exception as exc:
        logger.debug("PDF metadata unavailable: %s", exc)
    return result


class PageParser(HTMLParser):
    BLOCK_TAGS = {
        "article", "aside", "blockquote", "br", "div", "figcaption", "footer",
        "h1", "h2", "h3", "h4", "header", "li", "main", "p", "section",
        "table", "td", "th", "tr",
    }
    SKIP_TAGS = {"script", "style", "noscript", "svg"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta = {}
        self.title_parts = []
        self.text_parts = []
        self.links = []
        self._in_title = False
        self._skip_depth = 0
        self._current_link = None

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attrs = {str(k).lower(): v for k, v in attrs if k}
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "meta":
            key = (attrs.get("property") or attrs.get("name") or attrs.get("itemprop") or "").lower()
            content = attrs.get("content")
            if key and content and key not in self.meta:
                self.meta[key] = content.strip()
        elif tag == "title":
            self._in_title = True
        elif tag == "a":
            self._current_link = {"href": attrs.get("href", ""), "text": []}
        if tag in self.BLOCK_TAGS:
            self.text_parts.append("\n")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in self.SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag == "title":
            self._in_title = False
        elif tag == "a" and self._current_link is not None:
            self._current_link["text"] = " ".join(self._current_link["text"]).strip()
            self.links.append(self._current_link)
            self._current_link = None
        if tag in self.BLOCK_TAGS:
            self.text_parts.append("\n")

    def handle_data(self, data):
        if self._skip_depth:
            return
        clean = " ".join(data.split())
        if not clean:
            return
        if self._in_title:
            self.title_parts.append(clean)
        if self._current_link is not None:
            self._current_link["text"].append(clean)
        self.text_parts.append(clean + " ")


def first_value(mapping, keys):
    for key in keys:
        value = mapping.get(key.lower())
        if value:
            return value.strip()
    return ""


def clean_text(parts):
    text = unescape("".join(parts))
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def parse_html_page(html_text, final_url):
    parser = PageParser()
    parser.feed(html_text)
    meta = parser.meta
    page_text = clean_text(parser.text_parts)
    title = first_value(meta, ["og:title", "twitter:title", "headline"])
    if not title:
        title = " ".join(parser.title_parts).strip()
    authors = first_value(meta, ["author", "article:author", "byl"])
    published = first_value(
        meta,
        ["article:published_time", "datepublished", "date", "publishdate", "parsely-pub-date"],
    )
    site_name = first_value(meta, ["og:site_name", "application-name"])

    if not authors:
        match = re.search(r"\bAuthor:\s*([^\n|]{2,100})", page_text, re.IGNORECASE)
        if match:
            authors = match.group(1).strip()
    if not published:
        match = re.search(
            r"\bDate:\s*([A-Za-z]+\s+\d{1,2},\s+\d{4}|\d{4}-\d{2}-\d{2})",
            page_text,
            re.IGNORECASE,
        )
        if match:
            published = match.group(1).strip()
    if not published:
        match = re.search(r'"datePublished"\s*:\s*"([^"]+)"', html_text, re.IGNORECASE)
        if match:
            published = match.group(1).strip()

    links = []
    for link in parser.links:
        href = (link.get("href") or "").strip()
        if not href:
            continue
        absolute = urljoin(final_url, href)
        links.append({"url": absolute, "text": link.get("text", "")})

    pdf_links = []
    for link in links:
        parsed = urlparse(link["url"])
        looks_pdf = parsed.path.lower().endswith(".pdf") or ".pdf" in parsed.query.lower()
        label = link["text"].lower()
        if looks_pdf or label in {"paper", "pdf", "download paper", "full paper"}:
            if link["url"] not in [item["url"] for item in pdf_links]:
                pdf_links.append(link)

    path = urlparse(final_url).path.lower()
    og_type = first_value(meta, ["og:type"]).lower()
    is_blog = (
        og_type == "article"
        or bool(published)
        or any(token in path for token in ("/blog/", "/blogs/", "/posts/", "/article/"))
    )
    has_primary_paper_link = any(
        item["text"].strip().lower() in {"paper", "pdf", "full paper", "download paper"}
        for item in pdf_links
    )
    blog_path = any(token in path for token in ("/blog/", "/blogs/", "/posts/", "/article/"))
    if pdf_links and has_primary_paper_link and not blog_path:
        source_type = "project_page"
    elif is_blog:
        source_type = "blog"
    else:
        source_type = "webpage"

    selected_pdf = ""
    if source_type == "project_page":
        ranked = sorted(
            pdf_links,
            key=lambda item: (
                0 if item["text"].strip().lower() in {"paper", "pdf", "full paper"} else 1,
                len(item["url"]),
            ),
        )
        if ranked:
            selected_pdf = ranked[0]["url"]

    return {
        "source_type": source_type,
        "title": title,
        "authors": authors,
        "published_date": published,
        "site_name": site_name,
        "text": page_text,
        "linked_pdfs": [item["url"] for item in pdf_links],
        "selected_pdf_url": selected_pdf,
    }


def fetch_public_url(url, work_dir, max_pdf_bytes=MAX_PDF_BYTES):
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only public HTTP(S) URLs are supported")

    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/pdf;q=0.9,*/*;q=0.5"}
    with requests.get(url, headers=headers, stream=True, timeout=(15, 90), allow_redirects=True) as response:
        response.raise_for_status()
        final_url = response.url
        content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
        disposition = response.headers.get("Content-Disposition", "")
        iterator = response.iter_content(chunk_size=64 * 1024)
        first_chunk = next(iterator, b"")
        is_pdf = (
            first_chunk.startswith(b"%PDF-")
            or content_type == "application/pdf"
            or urlparse(final_url).path.lower().endswith(".pdf")
        )

        if is_pdf:
            suggested = parse_content_disposition(disposition)
            if not suggested:
                suggested = os.path.basename(urlparse(final_url).path)
            stem = safe_stem(Path(suggested or "document.pdf").stem, "document")
            pdf_path = Path(work_dir) / f"{stem}.pdf"
            total = 0
            with pdf_path.open("wb") as handle:
                for chunk in chain((first_chunk,), iterator):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > max_pdf_bytes:
                        raise ValueError(f"PDF exceeds {max_pdf_bytes} bytes")
                    handle.write(chunk)
            with pdf_path.open("rb") as handle:
                if handle.read(5) != b"%PDF-":
                    pdf_path.unlink(missing_ok=True)
                    raise ValueError(f"URL did not return a valid PDF (Content-Type: {content_type or '--'})")
            metadata = pdf_metadata(pdf_path)
            return {
                "kind": "pdf",
                "final_url": final_url,
                "content_type": content_type or "application/pdf",
                "local_pdf": str(pdf_path.resolve()),
                "content_length": total,
                **metadata,
            }

        body = bytearray(first_chunk)
        for chunk in iterator:
            if not chunk:
                continue
            body.extend(chunk)
            if len(body) > MAX_HTML_BYTES:
                raise ValueError(f"HTML exceeds {MAX_HTML_BYTES} bytes")
        encoding = response.encoding or "utf-8"
        html_text = bytes(body).decode(encoding, errors="replace")
        stem = safe_stem(Path(urlparse(final_url).path).name, "index")
        html_path = Path(work_dir) / f"{stem}.html"
        html_path.write_text(html_text, encoding="utf-8")
        page = parse_html_page(html_text, final_url)
        text_path = Path(work_dir) / f"{stem}.txt"
        text_path.write_text(page.pop("text"), encoding="utf-8")
        return {
            "kind": "html",
            "final_url": final_url,
            "content_type": content_type or "text/html",
            "local_html": str(html_path.resolve()),
            "local_text": str(text_path.resolve()),
            **page,
        }


def resolve_source(user_input, work_dir):
    original_input = user_input.strip()
    raw = extract_source_reference(original_input)
    if not raw:
        raise ValueError("Input is empty")

    work = Path(work_dir).resolve()
    work.mkdir(parents=True, exist_ok=True)

    local_path = Path(raw).expanduser()
    if local_path.exists():
        resolved = local_path.resolve()
        suffix = resolved.suffix.lower()
        if suffix == ".pdf":
            metadata = pdf_metadata(resolved)
            return {
                "source_type": "local_pdf",
                "original_input": original_input,
                "source_url": "",
                "canonical_url": "",
                "local_pdf": str(resolved),
                "document_id": stable_id("file", str(resolved).lower()),
                "arxiv_id": "",
                "title": metadata.get("title") or resolved.stem,
                "authors": metadata.get("authors", ""),
                "published_date": metadata.get("published_date", ""),
                "site_name": "",
                "linked_pdfs": [],
                "selected_pdf_url": "",
                "content_type": "application/pdf",
                "page_count": metadata.get("page_count"),
            }
        return {
            "source_type": "local_document",
            "original_input": original_input,
            "source_url": "",
            "canonical_url": "",
            "local_path": str(resolved),
            "document_id": stable_id("file", str(resolved).lower()),
            "arxiv_id": "",
            "title": resolved.stem,
            "authors": "",
            "published_date": "",
            "site_name": "",
            "linked_pdfs": [],
            "selected_pdf_url": "",
            "content_type": "",
        }

    arxiv_id = normalize_arxiv_id(raw)
    if arxiv_id:
        base_id = re.sub(r"v\d+$", "", arxiv_id, flags=re.IGNORECASE)
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
        result = {
            "source_type": "arxiv",
            "original_input": original_input,
            "source_url": f"https://arxiv.org/abs/{arxiv_id}",
            "canonical_url": f"https://arxiv.org/abs/{arxiv_id}",
            "pdf_url": pdf_url,
            "document_id": base_id,
            "arxiv_id": arxiv_id,
            "title": "",
            "authors": "",
            "published_date": "",
            "site_name": "arXiv",
            "linked_pdfs": [pdf_url],
            "selected_pdf_url": pdf_url,
            "content_type": "application/pdf",
        }
        try:
            fetched = fetch_public_url(pdf_url, work)
            result["local_pdf"] = fetched.get("local_pdf", "")
            result["page_count"] = fetched.get("page_count")
            result["content_length"] = fetched.get("content_length")
            # arXiv abstract endpoints may be rate-limited while the PDF is
            # still available. Preserve metadata embedded in the downloaded
            # PDF so downstream notes do not lose title and author fields.
            for field in ("title", "authors", "published_date"):
                if fetched.get(field):
                    result[field] = fetched[field]
        except Exception as exc:
            result["download_error"] = str(exc)
        return result

    parsed = urlparse(raw)
    if parsed.scheme in {"http", "https"}:
        fetched = fetch_public_url(raw, work)
        if fetched["kind"] == "pdf":
            result = {
                "source_type": "pdf_url",
                "original_input": original_input,
                "source_url": raw,
                "canonical_url": fetched["final_url"],
                "local_pdf": fetched["local_pdf"],
                "document_id": stable_id("url", fetched["final_url"]),
                "arxiv_id": "",
                "title": fetched.get("title") or Path(urlparse(fetched["final_url"]).path).stem,
                "authors": fetched.get("authors", ""),
                "published_date": fetched.get("published_date", ""),
                "site_name": parsed.hostname or "",
                "linked_pdfs": [fetched["final_url"]],
                "selected_pdf_url": fetched["final_url"],
                "content_type": fetched["content_type"],
                "page_count": fetched.get("page_count"),
                "content_length": fetched.get("content_length"),
            }
            final_parsed = urlparse(fetched["final_url"])
            parent_path = final_parsed.path.rsplit("/", 1)[0] + "/"
            landing_url = final_parsed._replace(path=parent_path, params="", query="", fragment="").geturl()
            if landing_url != fetched["final_url"]:
                try:
                    landing = fetch_public_url(landing_url, work)
                    if landing["kind"] == "html":
                        generic_title = Path(final_parsed.path).stem.lower()
                        current_title = (result.get("title") or "").strip()
                        if landing.get("title") and (not current_title or current_title.lower() == generic_title):
                            result["title"] = landing["title"]
                        if landing.get("authors") and not result.get("authors"):
                            result["authors"] = landing["authors"]
                        if landing.get("published_date") and not result.get("published_date"):
                            result["published_date"] = landing["published_date"]
                        result["landing_page_url"] = landing["final_url"]
                        result["local_landing_html"] = landing.get("local_html", "")
                        result["local_landing_text"] = landing.get("local_text", "")
                except Exception as exc:
                    result["landing_page_error"] = str(exc)
            return result

        result = {
            "source_type": fetched["source_type"],
            "original_input": original_input,
            "source_url": raw,
            "canonical_url": fetched["final_url"],
            "local_html": fetched["local_html"],
            "local_text": fetched["local_text"],
            "document_id": stable_id("url", fetched["final_url"]),
            "arxiv_id": "",
            "title": fetched.get("title", ""),
            "authors": fetched.get("authors", ""),
            "published_date": fetched.get("published_date", ""),
            "site_name": fetched.get("site_name") or (urlparse(fetched["final_url"]).hostname or ""),
            "linked_pdfs": fetched.get("linked_pdfs", []),
            "selected_pdf_url": fetched.get("selected_pdf_url", ""),
            "content_type": fetched["content_type"],
        }
        if result["source_type"] == "project_page" and result["selected_pdf_url"]:
            try:
                pdf = fetch_public_url(result["selected_pdf_url"], work)
                if pdf["kind"] == "pdf":
                    result["local_pdf"] = pdf["local_pdf"]
                    result["pdf_url"] = pdf["final_url"]
                    result["page_count"] = pdf.get("page_count")
            except Exception as exc:
                result["pdf_download_error"] = str(exc)
        return result

    return {
        "source_type": "title",
        "original_input": original_input,
        "source_url": "",
        "canonical_url": "",
        "document_id": stable_id("title", raw.lower()),
        "arxiv_id": "",
        "title": raw,
        "authors": "",
        "published_date": "",
        "site_name": "",
        "linked_pdfs": [],
        "selected_pdf_url": "",
        "content_type": "",
    }


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )
    parser = argparse.ArgumentParser(description="Resolve a research source into a typed local artifact")
    parser.add_argument("--input", required=True, help="arXiv ID/link, public URL, local file, or title")
    parser.add_argument("--work-dir", required=True, help="Writable temporary working directory")
    parser.add_argument("--output", default="-", help="JSON output path or - for stdout")
    args = parser.parse_args()

    try:
        result = resolve_source(args.input, args.work_dir)
    except (requests.RequestException, OSError, ValueError) as exc:
        logger.error("Source resolution failed: %s", exc)
        return 1

    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output == "-":
        print(payload)
    else:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload + "\n", encoding="utf-8")
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
