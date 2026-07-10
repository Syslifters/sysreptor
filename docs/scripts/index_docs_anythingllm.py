#!/usr/bin/env python3
"""Index SysReptor VitePress docs into AnythingLLM.

Local dry-run:
  cd docs
  pip install -r requirements.txt -r hooks/requirements.txt
  ANYTHINGLLM_API_KEY=... ANYTHINGLLM_WORKSPACE_SLUG=... \\
    python hooks/index_docs_anythingllm.py \\
      --sitemap docs/.vitepress/dist/sitemap.xml \\
      --docs-dir docs \\
      --dry-run
"""
from __future__ import annotations

import os
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import click
import requests
import yaml

from anythingllm_common import (
    DEFAULT_ANYTHINGLLM_BASE_URL,
    SLEEP_S_DEFAULT,
    TIMEOUT_S_DEFAULT,
    AnythingLLMClient,
    normalize_site_path,
    site_url_to_path,
)

DEFAULT_BASE_URL = "https://docs.sysreptor.com"
DEFAULT_UPLOAD_FOLDER = "sysreptor"

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_HEADING_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_MD_LINK_RE = re.compile(r"(\[[^\]]*\]\()([^)]+)(\))")
_HTML_HREF_RE = re.compile(r"""(href\s*=\s*)(["'])([^"']+)(\2)""", re.IGNORECASE)
_AUTODOC_PATH_RE = re.compile(r"python-library/(api|dataclasses)/")


@dataclass(frozen=True)
class PageDocument:
    url: str
    path: str
    markdown_path: Path
    upload_filename: str
    title: str
    description: str | None
    content: str


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


def _upload_filename(markdown_path: Path, docs_dir: Path) -> str:
    rel = markdown_path.relative_to(docs_dir)
    if rel.name == "index.md":
        rel = rel.parent / (rel.parent.name or "index")
    else:
        rel = rel.with_suffix("")
    return rel.as_posix()


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
    docs_dir: Path,
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
        upload_filename=_upload_filename(markdown_path, docs_dir),
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
            markdown_path, docs_dir=docs_dir, base_url=base_url, path=path
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
            markdown_path, docs_dir=docs_dir, base_url=base_url, path=path
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
            upload_filename=f"plugins/{plugin_slug}",
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


@click.command(help="Index SysReptor VitePress markdown into AnythingLLM.")
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
    "--anythingllm-base-url",
    default=DEFAULT_ANYTHINGLLM_BASE_URL,
    envvar="ANYTHINGLLM_BASE_URL",
    show_default=True,
    help="AnythingLLM instance base URL",
)
@click.option(
    "--workspace-slug",
    default="",
    envvar="ANYTHINGLLM_WORKSPACE_SLUG",
    help="Target workspace slug for embedding",
)
@click.option(
    "--upload-folder",
    default=DEFAULT_UPLOAD_FOLDER,
    envvar="ANYTHINGLLM_UPLOAD_FOLDER",
    show_default=True,
    help="AnythingLLM document folder for uploads",
)
@click.option("--timeout-s", type=float, default=TIMEOUT_S_DEFAULT, show_default=True)
@click.option("--sleep-s", type=float, default=SLEEP_S_DEFAULT, show_default=True)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Print URL to markdown mappings without uploading.",
)
def main(
    sitemap: Path,
    docs_dir: Path,
    plugins_dir: Path | None,
    plugins_github_base: str,
    base_url: str,
    anythingllm_base_url: str,
    workspace_slug: str,
    upload_folder: str,
    timeout_s: float,
    sleep_s: float,
    dry_run: bool,
) -> None:
    base_url = base_url.rstrip("/")
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

    api_key = os.environ.get("ANYTHINGLLM_API_KEY", "")
    if not api_key:
        click.echo("ANYTHINGLLM_API_KEY is required.", err=True)
        raise SystemExit(2)
    if not workspace_slug:
        click.echo("ANYTHINGLLM_WORKSPACE_SLUG is required.", err=True)
        raise SystemExit(2)

    client = AnythingLLMClient(
        base_url=anythingllm_base_url,
        api_key=api_key,
        workspace_slug=workspace_slug,
        upload_folder=upload_folder,
        timeout_s=timeout_s,
    )

    click.echo("Purging previous documents...")
    client.purge_upload_folder()

    failures = 0
    total = len(documents)
    for index, document in enumerate(documents, start=1):
        try:
            filename = document.upload_filename
            content = document.content
            if _is_autodoc_page(document.markdown_path) and autodoc_script.is_file():
                content = _expand_autodoc_content(content, autodoc_script)
            content = _prepare_upload_content(content, document.url)
            client.upload_markdown(
                filename=filename,
                content=content,
                url=document.url,
                title=document.title,
                description=document.description,
            )
            click.echo(f"Uploaded {index}/{total}: {document.url}")
        except (requests.RequestException, RuntimeError, subprocess.SubprocessError) as exc:
            failures += 1
            click.echo(
                f"ERR {index}/{total} {document.url} ({document.markdown_path}): {exc}",
                err=True,
            )
        if sleep_s:
            time.sleep(sleep_s)

    if failures:
        click.echo(
            f"Failed to upload {failures}/{total} document(s).",
            err=True,
        )
        raise SystemExit(2)

    click.echo(f"Indexed {total} page(s) into AnythingLLM.")


if __name__ == "__main__":
    main()
