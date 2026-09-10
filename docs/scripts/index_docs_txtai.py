#!/usr/bin/env python3
"""Index SysReptor VitePress docs into txtai-chat via the Index API.

Local dry-run:
  cd docs
  pip install -r requirements.txt
  python scripts/index_docs_txtai.py \\
    --sitemap docs/.vitepress/dist/sitemap.xml \\
    --docs-dir docs \\
    --dry-run
"""
from __future__ import annotations

import os
import re
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import click
import requests
import yaml

DEFAULT_BASE_URL = "https://docs.sysreptor.com"
DEFAULT_TXTAI_BASE_URL = "https://sysreptor-ai.internal.syslifters.com"
DEFAULT_FOLDER = "sysreptor-docs"
TIMEOUT_S_DEFAULT = 300.0
BATCH_SIZE_DEFAULT = 5

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_HEADING_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_MD_LINK_RE = re.compile(r"(\[[^\]]*\]\()([^)]+)(\))")
_HTML_HREF_RE = re.compile(r"""(href\s*=\s*)(["'])([^"']+)(\2)""", re.IGNORECASE)
_AUTODOC_PATH_RE = re.compile(r"python-library/(api|dataclasses)/")


def normalize_base_url(url: str) -> str:
    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or ""
    return f"{scheme}://{netloc}{path}"


def normalize_site_path(path: str) -> str:
    if not path:
        return "/"
    if not path.startswith("/"):
        path = f"/{path}"
    if path != "/":
        path = path.rstrip("/")
    if path.endswith(".md"):
        path = path[:-3] or "/"
    return path


def site_url_to_path(url: str, base_url: str) -> str | None:
    normalized_url = normalize_base_url(url)
    normalized_base = normalize_base_url(base_url)
    if not normalized_url.startswith(normalized_base):
        return None
    suffix = normalized_url[len(normalized_base) :]
    return normalize_site_path(suffix)


@dataclass(frozen=True)
class PageDocument:
    url: str
    path: str
    markdown_path: Path
    title: str
    description: str | None
    content: str


class TxtaiIndexClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_token: str,
        timeout_s: float,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    def begin_reindex(self, folder: str) -> str:
        response = self.session.post(
            f"{self.base_url}/v1/index/folders/{folder}/reindex",
            timeout=self.timeout_s,
        )
        response.raise_for_status()
        payload = response.json()
        reindex_id = payload.get("reindex_id")
        if not reindex_id:
            raise RuntimeError(f"Missing reindex_id in begin response: {payload!r}")
        return str(reindex_id)

    def upsert_documents(
        self,
        *,
        folder: str,
        documents: list[dict[str, str]],
        mode: str,
        reindex_id: str | None = None,
    ) -> dict:
        body: dict = {
            "folder": folder,
            "mode": mode,
            "documents": documents,
        }
        if reindex_id is not None:
            body["reindex_id"] = reindex_id
        response = self.session.post(
            f"{self.base_url}/v1/index/documents",
            json=body,
            timeout=self.timeout_s,
        )
        response.raise_for_status()
        return response.json()

    def commit_reindex(self, folder: str, reindex_id: str) -> dict:
        response = self.session.post(
            f"{self.base_url}/v1/index/folders/{folder}/reindex/{reindex_id}/commit",
            timeout=self.timeout_s,
        )
        response.raise_for_status()
        return response.json() if response.content else {}

    def abort_reindex(self, folder: str, reindex_id: str) -> None:
        response = self.session.delete(
            f"{self.base_url}/v1/index/folders/{folder}/reindex/{reindex_id}",
            timeout=self.timeout_s,
        )
        response.raise_for_status()


def _parse_sitemap_urls(sitemap_path: Path, base_url: str) -> list[str]:
    root = ET.parse(sitemap_path).getroot()
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = [el.text.strip() for el in root.findall(".//sm:loc", ns) if el.text]
    if not locs:
        locs = [el.text.strip() for el in root.findall(".//loc") if el.text]

    urls: list[str] = []
    seen: set[str] = set()
    for loc in locs:
        path = site_url_to_path(loc, base_url)
        if path is None:
            continue
        if path == "/s" or path.startswith("/s/"):
            continue
        canonical = base_url.rstrip("/") + ("" if path == "/" else path)
        if canonical in seen:
            continue
        seen.add(canonical)
        urls.append(canonical)
    return sorted(urls, key=lambda u: (u != base_url.rstrip("/") + "/", u))


def _resolve_markdown_path(docs_dir: Path, site_path: str) -> Path | None:
    site_path = normalize_site_path(site_path)
    if site_path == "/de" or site_path.startswith("/de/"):
        base = docs_dir / "de"
        rel = site_path[len("/de") :] or "/"
    else:
        base = docs_dir
        rel = site_path

    if rel == "/":
        candidates = [base / "index.md"]
    else:
        rel = rel.lstrip("/")
        candidates = [base / f"{rel}.md", base / rel / "index.md"]

    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    raw = match.group(1)
    body = text[match.end() :]
    try:
        meta = yaml.safe_load(raw) or {}
    except yaml.YAMLError:
        meta = {}
    if not isinstance(meta, dict):
        meta = {}
    return meta, body


def _derive_title(markdown_path: Path, meta: dict, body: str) -> str:
    title = meta.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    heading = _HEADING_RE.search(body)
    if heading:
        return heading.group(1).strip()
    if markdown_path.name == "index.md":
        return markdown_path.parent.name
    return markdown_path.stem


def _derive_description(meta: dict) -> str | None:
    description = meta.get("description")
    if isinstance(description, str) and description.strip():
        return description.strip()
    return None


def _is_rewritable_href(href: str) -> bool:
    href = href.strip()
    if not href or href.startswith(("#", "mailto:", "tel:")):
        return False
    lower = href.lower()
    return not lower.startswith(("http://", "https://", "//"))


def _strip_md_from_href(href: str) -> str:
    if not _is_rewritable_href(href):
        return href
    fragment = ""
    query = ""
    path = href
    if "#" in path:
        path, fragment = path.split("#", 1)
        fragment = f"#{fragment}"
    if "?" in path:
        path, query = path.split("?", 1)
        query = f"?{query}"
    if path.endswith(".md"):
        path = path[:-3] or "/"
    if path == "/index" or path.endswith("/index"):
        path = path[: -len("/index")] or "/"
    elif path == "index":
        path = "."
    return f"{path}{query}{fragment}"


def _rewrite_internal_md_links(content: str) -> str:
    def rewrite_markdown_link(match: re.Match[str]) -> str:
        href = match.group(2).strip()
        return f"{match.group(1)}{_strip_md_from_href(href)}{match.group(3)}"

    def rewrite_html_href(match: re.Match[str]) -> str:
        href = match.group(3).strip()
        return f"{match.group(1)}{match.group(2)}{_strip_md_from_href(href)}{match.group(2)}"

    content = _MD_LINK_RE.sub(rewrite_markdown_link, content)
    return _HTML_HREF_RE.sub(rewrite_html_href, content)


def _with_canonical_url(content: str, url: str) -> str:
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return content
    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return content
    if not isinstance(meta, dict):
        return content
    meta["url"] = url
    body = content[match.end() :]
    dumped = yaml.dump(
        meta, default_flow_style=False, allow_unicode=True, sort_keys=False
    ).rstrip()
    return f"---\n{dumped}\n---\n{body}"


def _prepare_upload_content(content: str, url: str) -> str:
    content = _with_canonical_url(content, url)
    return _rewrite_internal_md_links(content)


def _is_autodoc_page(markdown_path: Path) -> bool:
    return bool(_AUTODOC_PATH_RE.search(markdown_path.as_posix()))


def _expand_autodoc_content(content: str, autodoc_script: Path) -> str:
    result = subprocess.run(
        ["python3", str(autodoc_script), "expand", "--no-cache"],
        input=content,
        capture_output=True,
        text=True,
        check=False,
        cwd=autodoc_script.parent.parent,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown error"
        raise RuntimeError(f"Failed to expand autodoc blocks: {message}")
    return result.stdout


def _document_from_markdown(
    markdown_path: Path,
    *,
    base_url: str,
    path: str,
) -> PageDocument:
    raw = markdown_path.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(raw)
    canonical_url = base_url.rstrip("/") + ("" if path == "/" else path)
    return PageDocument(
        url=canonical_url,
        path=path,
        markdown_path=markdown_path,
        title=_derive_title(markdown_path, meta, body),
        description=_derive_description(meta),
        content=raw,
    )


def _build_documents(
    urls: list[str], docs_dir: Path, base_url: str
) -> tuple[list[PageDocument], list[str]]:
    documents: list[PageDocument] = []
    unmapped: list[str] = []

    for url in urls:
        path = site_url_to_path(url, base_url)
        if path is None:
            unmapped.append(url)
            continue
        markdown_path = _resolve_markdown_path(docs_dir, path)
        if markdown_path is None:
            unmapped.append(url)
            continue
        documents.append(_document_from_markdown(
            markdown_path, base_url=base_url, path=path
        ))

    return documents, unmapped


def _build_cli_documents(
    docs_dir: Path, base_url: str, seen_urls: set[str]
) -> list[PageDocument]:
    cli_dir = docs_dir / "cli"
    if not cli_dir.is_dir():
        return []

    documents: list[PageDocument] = []
    for markdown_path in sorted(cli_dir.rglob("*.md")):
        rel = markdown_path.relative_to(cli_dir)
        if rel.name == "index.md":
            path = "/" + rel.parent.as_posix()
            if path == "/.":
                path = "/cli"
            else:
                path = f"/cli/{rel.parent.as_posix()}"
        else:
            path = f"/cli/{rel.with_suffix('').as_posix()}"

        canonical_url = base_url.rstrip("/") + ("" if path == "/" else path)
        if canonical_url in seen_urls:
            continue
        seen_urls.add(canonical_url)
        documents.append(_document_from_markdown(
            markdown_path, base_url=base_url, path=path
        ))

    return documents


def _build_plugin_documents(
    plugins_dir: Path,
    *,
    plugins_github_base: str,
) -> list[PageDocument]:
    if not plugins_dir.is_dir():
        return []

    documents: list[PageDocument] = []
    base = plugins_github_base.rstrip("/")
    for markdown_path in sorted(plugins_dir.glob("*/README.md")):
        plugin_slug = markdown_path.parent.name
        raw = markdown_path.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(raw)
        url = f"{base}/{plugin_slug}/README.md"
        documents.append(PageDocument(
            url=url,
            path=f"/plugins/{plugin_slug}",
            markdown_path=markdown_path,
            title=_derive_title(markdown_path, meta, body),
            description=_derive_description(meta),
            content=raw,
        ))
    return documents


def _merge_documents(
    sitemap: Path,
    docs_dir: Path,
    base_url: str,
    *,
    plugins_dir: Path | None = None,
    plugins_github_base: str = "",
) -> tuple[list[PageDocument], list[str]]:
    urls = _parse_sitemap_urls(sitemap, base_url)
    documents, unmapped = _build_documents(urls, docs_dir, base_url)
    seen_urls = {doc.url for doc in documents}
    documents.extend(_build_cli_documents(docs_dir, base_url, seen_urls))
    if plugins_dir and plugins_github_base:
        documents.extend(_build_plugin_documents(
            plugins_dir, plugins_github_base=plugins_github_base
        ))
    return documents, unmapped


def _to_index_payload(document: PageDocument, autodoc_script: Path) -> dict[str, str]:
    content = document.content
    if _is_autodoc_page(document.markdown_path) and autodoc_script.is_file():
        content = _expand_autodoc_content(content, autodoc_script)
    return {
        "id": document.url,
        "text": _prepare_upload_content(content, document.url),
        "source": document.url,
    }


@click.command(help="Index SysReptor VitePress markdown into txtai-chat via the Index API.")
@click.option(
    "--sitemap",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to built sitemap.xml",
)
@click.option(
    "--docs-dir",
    default="docs",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    show_default=True,
    help="Path to VitePress docs source",
)
@click.option(
    "--plugins-dir",
    default=None,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Optional: root directory containing plugin subdirectories with README.md files.",
)
@click.option(
    "--plugins-github-base",
    default="https://github.com/Syslifters/sysreptor/blob/main/plugins",
    show_default=True,
    help="Base GitHub URL used to construct plugin README source links.",
)
@click.option(
    "--base-url",
    default=DEFAULT_BASE_URL,
    envvar="BASE_URL",
    show_default=True,
    help="Public base URL for canonical links",
)
@click.option(
    "--txtai-base-url",
    default=DEFAULT_TXTAI_BASE_URL,
    envvar="TXTAI_BASE_URL",
    show_default=True,
    help="txtai-chat server base URL",
)
@click.option(
    "--folder",
    default=DEFAULT_FOLDER,
    envvar="TXTAI_INDEX_FOLDER",
    show_default=True,
    help="Index folder namespace for the full reindex",
)
@click.option(
    "--batch-size",
    type=int,
    default=BATCH_SIZE_DEFAULT,
    show_default=True,
    help="Documents per POST /v1/index/documents request",
)
@click.option("--timeout-s", type=float, default=TIMEOUT_S_DEFAULT, show_default=True)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Print URL to markdown mappings without indexing.",
)
def main(
    sitemap: Path,
    docs_dir: Path,
    plugins_dir: Path | None,
    plugins_github_base: str,
    base_url: str,
    txtai_base_url: str,
    folder: str,
    batch_size: int,
    timeout_s: float,
    dry_run: bool,
) -> None:
    base_url = base_url.rstrip("/")
    if batch_size < 1:
        click.echo("--batch-size must be >= 1.", err=True)
        raise SystemExit(2)

    docs_dir = docs_dir.resolve()
    autodoc_script = docs_dir.parent / "scripts" / "python_autodoc.py"

    plugins_dir = plugins_dir.resolve() if plugins_dir else None
    documents, unmapped = _merge_documents(
        sitemap,
        docs_dir,
        base_url,
        plugins_dir=plugins_dir,
        plugins_github_base=plugins_github_base,
    )

    if unmapped:
        click.echo("Unmapped sitemap URLs:", err=True)
        for url in unmapped:
            click.echo(f"  - {url}", err=True)
    click.echo(f"Mapped {len(documents)} page(s) from {sitemap} and CLI docs.")

    if dry_run:
        for doc in documents:
            click.echo(f"{doc.url} -> {doc.markdown_path} ({doc.title})")
        return

    api_token = os.environ.get("TXTAI_INDEX_API_TOKEN", "")
    if not api_token:
        click.echo("TXTAI_INDEX_API_TOKEN is required.", err=True)
        raise SystemExit(2)

    client = TxtaiIndexClient(
        base_url=txtai_base_url,
        api_token=api_token,
        timeout_s=timeout_s,
    )

    try:
        reindex_id = client.begin_reindex(folder)
    except requests.RequestException as exc:
        click.echo(f"ERR begin reindex for folder {folder!r}: {exc}", err=True)
        raise SystemExit(2) from exc

    click.echo(f"Started full reindex for folder {folder!r} ({reindex_id}).")

    failures = 0
    total = len(documents)
    indexed = 0
    for start in range(0, total, batch_size):
        batch = documents[start : start + batch_size]
        batch_end = start + len(batch)
        try:
            payload = [_to_index_payload(doc, autodoc_script) for doc in batch]
            result = client.upsert_documents(
                folder=folder,
                documents=payload,
                mode="full",
                reindex_id=reindex_id,
            )
            count = int(result.get("count", len(batch)))
            indexed += count
            click.echo(
                f"Indexed {start + 1}-{batch_end}/{total}"
                f" ({count} document(s) in batch)."
            )
        except (requests.RequestException, RuntimeError, subprocess.SubprocessError) as exc:
            failures += len(batch)
            click.echo(
                f"ERR batch {start + 1}-{batch_end}/{total}: {exc}",
                err=True,
            )

    if failures:
        try:
            client.abort_reindex(folder, reindex_id)
            click.echo(
                f"Aborted reindex {reindex_id} (orphans not deleted).",
                err=True,
            )
        except requests.RequestException as exc:
            click.echo(f"ERR abort reindex {reindex_id}: {exc}", err=True)
        click.echo(
            f"Failed to index {failures}/{total} document(s).",
            err=True,
        )
        raise SystemExit(2)

    try:
        client.commit_reindex(folder, reindex_id)
    except requests.RequestException as exc:
        click.echo(f"ERR commit reindex {reindex_id}: {exc}", err=True)
        try:
            client.abort_reindex(folder, reindex_id)
            click.echo(
                f"Aborted reindex {reindex_id} after commit failure.",
                err=True,
            )
        except requests.RequestException as abort_exc:
            click.echo(f"ERR abort reindex {reindex_id}: {abort_exc}", err=True)
        raise SystemExit(2) from exc

    click.echo(
        f"Committed full reindex for folder {folder!r}:"
        f" {indexed} page(s) indexed, orphans removed."
    )


if __name__ == "__main__":
    main()
