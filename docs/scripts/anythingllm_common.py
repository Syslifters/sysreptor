from __future__ import annotations

import json
from urllib.parse import urlparse

import requests

TIMEOUT_S_DEFAULT = 60.0
SLEEP_S_DEFAULT = 0.1
DEFAULT_ANYTHINGLLM_BASE_URL = "https://anythingllm.internal.syslifters.com"


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


class AnythingLLMClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        workspace_slug: str,
        upload_folder: str,
        timeout_s: float,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.workspace_slug = workspace_slug
        self.upload_folder = upload_folder
        self.timeout_s = timeout_s
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            }
        )

    def _url(self, path: str) -> str:
        return f"{self.base_url}/api{path}"

    def get_workspace(self) -> dict:
        response = self.session.get(
            self._url(f"/v1/workspace/{self.workspace_slug}"),
            timeout=self.timeout_s,
        )
        response.raise_for_status()
        payload = response.json()
        workspace = payload.get("workspace")[0] if payload.get("workspace") else None
        if workspace and not isinstance(workspace, dict):
            raise RuntimeError(f"Unexpected workspace response: {payload!r}")
        return workspace or {}

    def delete_workspace_documents(self, docpaths: list[str]) -> None:
        if not docpaths:
            return
        response = self.session.post(
            self._url(f"/v1/workspace/{self.workspace_slug}/update-embeddings"),
            json={"adds": [], "deletes": docpaths},
            timeout=self.timeout_s,
        )
        response.raise_for_status()

    def purge_upload_folder(self) -> None:
        workspace = self.get_workspace()
        prefix = f"{self.upload_folder}/"
        deletes = [
            doc["docpath"]
            for doc in workspace.get("documents", [])
            if isinstance(doc, dict)
            and isinstance(doc.get("docpath"), str)
            and doc["docpath"].startswith(prefix)
        ]

        if deletes:
            self.delete_workspace_documents(deletes)
            print(f"Removed {len(deletes)} existing document(s) from workspace.")

        response = self.session.request(
            "DELETE",
            self._url("/v1/document/remove-folder"),
            json={"name": self.upload_folder},
            timeout=self.timeout_s,
        )
        if response.status_code >= 400 and response.status_code != 404:
            response.raise_for_status()
        elif response.ok:
            print(f"Removed folder '{self.upload_folder}' from document storage.")

    def upload_markdown(
        self,
        *,
        filename: str,
        content: str,
        url: str,
        title: str,
        description: str | None = None,
    ) -> None:
        metadata: dict[str, str] = {
            "title": title,
            "url": url,
            "docSource": url,
            "chunkSource": f"link://{url}",
        }
        if description:
            metadata["description"] = description

        files = {
            "file": (filename, content.encode("utf-8"), "text/markdown"),
        }
        data = {
            "addToWorkspaces": self.workspace_slug,
            "metadata": json.dumps(metadata),
        }
        response = self.session.post(
            self._url(f"/v1/document/upload/{self.upload_folder}"),
            files=files,
            data=data,
            timeout=self.timeout_s,
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("success", False):
            raise RuntimeError(
                f"Upload failed for {url}: {payload.get('error') or payload}"
            )
