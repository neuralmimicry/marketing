#!/usr/bin/env python3
"""Submit Refiner-backed marketing jobs and transcribe captured media."""

from __future__ import annotations

import argparse
import http.cookiejar
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = REPO_ROOT / "catalog" / "products.json"
DEFAULT_REFINER_BASE_URL = os.environ.get("REFINER_BASE_URL", "http://127.0.0.1:5001")
DEFAULT_HTTP_TIMEOUT = float(os.environ.get("REFINER_HTTP_TIMEOUT", "60"))
ACTIVE_JOB_STATUSES = {"dispatching", "paused", "queued", "running"}


class RefinerAPIError(RuntimeError):
    """Raised when the Refiner API returns a non-success response."""

    def __init__(self, status: int, body: str):
        self.status = status
        self.body = body
        super().__init__(f"Refiner API request failed with status {status}")


class RefinerClient:
    """Small HTTP client for Refiner's authenticated and STT routes."""

    def __init__(
        self,
        *,
        base_url: str,
        access_token: str | None = None,
        cookie_jar_path: Path | None = None,
        timeout: float = DEFAULT_HTTP_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.access_token = (access_token or "").strip() or None
        self.timeout = timeout
        self.cookie_jar_path = cookie_jar_path.expanduser() if cookie_jar_path else None
        if self.cookie_jar_path:
            self.cookie_jar = http.cookiejar.MozillaCookieJar(str(self.cookie_jar_path))
            if self.cookie_jar_path.exists():
                self.cookie_jar.load(ignore_discard=True, ignore_expires=True)
        else:
            self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie_jar))

    def _save_cookies(self) -> None:
        if isinstance(self.cookie_jar, http.cookiejar.MozillaCookieJar) and self.cookie_jar_path:
            self.cookie_jar_path.parent.mkdir(parents=True, exist_ok=True)
            self.cookie_jar.save(ignore_discard=True, ignore_expires=True)

    def _request(
        self,
        method: str,
        path: str,
        *,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        include_access_token: bool = True,
    ) -> tuple[int, bytes]:
        request_headers = {
            "Accept": "application/json",
            "User-Agent": "marketing-refiner-client/1",
        }
        if headers:
            request_headers.update(headers)
        if include_access_token and self.access_token:
            request_headers["Authorization"] = f"Bearer {self.access_token}"
        request = urllib.request.Request(
            url=f"{self.base_url}{path}",
            data=data,
            headers=request_headers,
            method=method,
        )
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                payload = response.read()
                self._save_cookies()
                return int(getattr(response, "status", 200) or 200), payload
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RefinerAPIError(int(exc.code), body) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Unable to reach Refiner at {self.base_url}: {exc.reason}") from exc

    def request_json(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        include_access_token: bool = True,
    ) -> dict[str, Any]:
        encoded = None
        request_headers = dict(headers or {})
        if payload is not None:
            encoded = json.dumps(payload).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json")
        _, raw = self._request(
            method,
            path,
            data=encoded,
            headers=request_headers,
            include_access_token=include_access_token,
        )
        return decode_json(raw)

    def request_form(
        self,
        method: str,
        path: str,
        *,
        fields: dict[str, Any],
        headers: dict[str, str] | None = None,
        include_access_token: bool = False,
    ) -> tuple[int, bytes]:
        encoded = urllib.parse.urlencode(fields).encode("utf-8")
        request_headers = {"Content-Type": "application/x-www-form-urlencoded"}
        if headers:
            request_headers.update(headers)
        return self._request(
            method,
            path,
            data=encoded,
            headers=request_headers,
            include_access_token=include_access_token,
        )

    def request_multipart(
        self,
        method: str,
        path: str,
        *,
        fields: dict[str, Any],
        files: list[tuple[str, str, bytes, str]],
        include_access_token: bool = True,
    ) -> dict[str, Any]:
        body, content_type = encode_multipart(fields, files)
        _, raw = self._request(
            method,
            path,
            data=body,
            headers={"Content-Type": content_type},
            include_access_token=include_access_token,
        )
        return decode_json(raw)

    def login(self, username: str, password: str) -> None:
        self.request_form(
            "POST",
            "/api/login",
            fields={
                "username": username,
                "password": password,
                "next": "/",
            },
            headers={"Accept": "text/html,application/json"},
            include_access_token=False,
        )
        session_payload = self.request_json("GET", "/api/session")
        if not session_payload.get("authenticated"):
            raise RuntimeError("Refiner login did not establish an authenticated session")

    def ensure_authenticated(self) -> dict[str, Any]:
        session_payload = self.request_json("GET", "/api/session")
        if not session_payload.get("authenticated"):
            raise RuntimeError(
                "Refiner job submission requires authentication. Use --username/--password, "
                "--cookie-jar, or --refiner-access-token."
            )
        return session_payload


def load_catalog() -> dict[str, Any]:
    with CATALOG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def product_map() -> dict[str, dict[str, Any]]:
    catalog = load_catalog()
    return {entry["slug"]: entry for entry in catalog.get("products", [])}


def load_manifest(product: str) -> dict[str, Any]:
    manifest_path = REPO_ROOT / "videos" / "manifests" / f"{product}.json"
    with manifest_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def resolve_path(value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (REPO_ROOT / candidate)


def ensure_paths(paths: list[Path]) -> None:
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required paths:\n- " + "\n- ".join(missing))


def find_deliverable(manifest: dict[str, Any], kind: str) -> dict[str, Any]:
    for item in manifest.get("deliverables", []):
        if item.get("kind") == kind:
            return item
    raise KeyError(f"No deliverable with kind={kind!r}")


def build_context(product: dict[str, Any], extra_context: list[str]) -> list[str]:
    paths = [str(resolve_path(path).resolve()) for path in product.get("context_files", [])]
    for item in extra_context:
        paths.append(str(resolve_path(item).resolve()))
    seen = set()
    ordered: list[str] = []
    for path in paths:
        if path not in seen:
            ordered.append(path)
            seen.add(path)
    return ordered


def list_targets() -> int:
    products = product_map()
    for slug, product in sorted(products.items()):
        manifest = load_manifest(slug)
        print(f"{slug}: {product['name']}")
        for deliverable in manifest.get("deliverables", []):
            prompt = deliverable.get("prompt_file", "")
            print(f"  - {deliverable['kind']}: {deliverable['title']} ({prompt})")
    return 0


def decode_json(raw: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        text = raw.decode("utf-8", errors="replace")
        raise RuntimeError(f"Expected a JSON response from Refiner, got: {text[:240]}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("Expected a JSON object from Refiner")
    return payload


def encode_multipart(
    fields: dict[str, Any],
    files: list[tuple[str, str, bytes, str]],
) -> tuple[bytes, str]:
    boundary = f"----refiner-boundary-{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for key, value in fields.items():
        if value is None:
            continue
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"),
                str(value).encode("utf-8"),
                b"\r\n",
            ]
        )
    for field_name, filename, content, content_type in files:
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                (
                    f'Content-Disposition: form-data; name="{field_name}"; '
                    f'filename="{filename}"\r\n'
                ).encode("utf-8"),
                f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
                content,
                b"\r\n",
            ]
        )
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(text)


def build_client(args: argparse.Namespace, *, prefer_stt_token: bool = False) -> RefinerClient:
    cookie_jar = Path(args.cookie_jar).expanduser() if getattr(args, "cookie_jar", None) else None
    access_token = None
    if prefer_stt_token:
        access_token = (getattr(args, "stt_token", None) or "").strip() or None
    if not access_token:
        access_token = (getattr(args, "refiner_access_token", None) or "").strip() or None
    client = RefinerClient(
        base_url=args.refiner_base_url,
        access_token=access_token,
        cookie_jar_path=cookie_jar,
        timeout=args.http_timeout,
    )
    username = (getattr(args, "username", None) or "").strip()
    password = (getattr(args, "password", None) or "").strip()
    if username:
        if not password:
            raise RuntimeError("--username requires --password or REFINER_PASSWORD")
        client.login(username, password)
    return client


def auth_mode(args: argparse.Namespace, *, prefer_stt_token: bool = False) -> str:
    if prefer_stt_token and (getattr(args, "stt_token", None) or "").strip():
        return "stt bearer token"
    if (getattr(args, "refiner_access_token", None) or "").strip():
        return "bearer token"
    if (getattr(args, "username", None) or "").strip():
        return "login session"
    if getattr(args, "cookie_jar", None):
        return "cookie jar"
    return "none"


def build_job_payload(
    *,
    product: dict[str, Any],
    kind: str,
    prompt_text: str,
    context_paths: list[str],
    draft_path: Path,
    references_path: Path,
    max_iterations: int,
    allow_live_discovery: bool,
    llm_provider: str | None,
    llm_model: str | None,
    llm_reasoning_effort: str | None,
    token_scope: str | None,
    team_id: str | None,
    refiner_dry_run: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "workflow": "topic_research",
        "project_name": f"{product['name']} {kind.title()} Marketing Draft",
        "topic_source": prompt_text,
        "topic_output": str(draft_path),
        "references_output": str(references_path),
        "max_iterations": max_iterations,
        "context_sources": context_paths,
    }
    if not allow_live_discovery:
        payload["disable_jira"] = True
        payload["disable_confluence"] = True
    if llm_provider:
        payload["llm_provider"] = llm_provider
    if llm_model:
        payload["llm_model"] = llm_model
    if llm_reasoning_effort:
        payload["llm_reasoning_effort"] = llm_reasoning_effort
    if token_scope:
        payload["token_scope"] = token_scope
    if team_id:
        payload["team_id"] = team_id
    if refiner_dry_run:
        payload["extra_args"] = "--dry-run"
    return payload


def wait_for_job(
    client: RefinerClient,
    *,
    job_id: str,
    job_path: Path,
    poll_interval: float,
    wait_timeout: float | None,
) -> dict[str, Any]:
    started = time.monotonic()
    last_status: tuple[str | None, Any] | None = None
    while True:
        detail = client.request_json("GET", f"/api/jobs/{urllib.parse.quote(job_id, safe='')}")
        write_json(job_path, detail)
        status = str(detail.get("status") or "unknown").strip().lower() or "unknown"
        progress = detail.get("progress")
        marker = (status, progress)
        if marker != last_status:
            if progress is None:
                print(f"Job {job_id}: {status}")
            else:
                print(f"Job {job_id}: {status} (progress={progress})")
            last_status = marker
        if status not in ACTIVE_JOB_STATUSES:
            return detail
        if wait_timeout is not None and (time.monotonic() - started) > wait_timeout:
            raise TimeoutError(f"Timed out waiting for Refiner job {job_id}")
        time.sleep(poll_interval)


def draft_video(args: argparse.Namespace) -> int:
    products = product_map()
    if args.product not in products:
        raise KeyError(f"Unknown product {args.product!r}")

    product = products[args.product]
    manifest = load_manifest(args.product)
    deliverable = find_deliverable(manifest, args.kind)
    prompt_path = resolve_path(deliverable["prompt_file"]).resolve()
    context_paths = build_context(product, args.context_extra or [])
    ensure_paths([prompt_path, *[Path(path) for path in context_paths]])

    output_dir = (REPO_ROOT / "build" / "refiner" / args.product / args.kind).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    draft_path = output_dir / f"{args.product}-{args.kind}-draft.md"
    references_path = output_dir / f"{args.product}-{args.kind}-references.md"
    job_path = output_dir / f"{args.product}-{args.kind}-job.json"
    prompt_text = prompt_path.read_text(encoding="utf-8")
    if args.token_scope == "team" and not args.team_id:
        raise RuntimeError("--token-scope team requires --team-id")

    payload = build_job_payload(
        product=product,
        kind=args.kind,
        prompt_text=prompt_text,
        context_paths=context_paths,
        draft_path=draft_path,
        references_path=references_path,
        max_iterations=args.max_iterations,
        allow_live_discovery=args.allow_live_discovery,
        llm_provider=args.llm_provider,
        llm_model=args.llm_model,
        llm_reasoning_effort=args.llm_reasoning_effort,
        token_scope=args.token_scope,
        team_id=args.team_id,
        refiner_dry_run=args.refiner_dry_run,
    )

    print(f"Product: {product['name']}")
    print(f"Kind: {args.kind}")
    print(f"Prompt: {prompt_path}")
    print(f"Draft output: {draft_path}")
    print(f"References output: {references_path}")
    print(f"Job metadata: {job_path}")
    print(f"Refiner base URL: {args.refiner_base_url}")
    print(f"Auth mode: {auth_mode(args)}")
    print("Context files:")
    for item in context_paths:
        print(f"- {item}")
    print("Job payload:")
    print(json.dumps(payload, indent=2, sort_keys=True))
    sys.stdout.flush()

    if args.print_only:
        return 0

    client = build_client(args)
    session_payload = client.ensure_authenticated()
    print(f"Authenticated as: {session_payload.get('user')}")
    job = client.request_json("POST", "/api/jobs", payload=payload)
    write_json(job_path, job)
    job_id = str(job.get("id") or job.get("job_id") or "").strip()
    if not job_id:
        raise RuntimeError("Refiner did not return a job id")
    print(f"Submitted Refiner job: {job_id}")

    if not args.wait:
        return 0

    final_job = wait_for_job(
        client,
        job_id=job_id,
        job_path=job_path,
        poll_interval=args.poll_interval,
        wait_timeout=args.wait_timeout,
    )
    final_status = str(final_job.get("status") or "unknown").strip().lower() or "unknown"
    exit_code = final_job.get("exit_code")
    print(f"Final status: {final_status}")
    print(f"Draft output: {draft_path}")
    print(f"References output: {references_path}")
    print(f"Job metadata: {job_path}")
    if final_status == "completed" and (exit_code is None or int(exit_code) == 0):
        return 0
    return int(exit_code) if isinstance(exit_code, int) and exit_code != 0 else 1


def transcribe_media(args: argparse.Namespace) -> int:
    input_path = resolve_path(args.input_file).resolve()
    ensure_paths([input_path])
    output_json = resolve_path(args.output_json).resolve() if args.output_json else None
    output_text = resolve_path(args.output_text).resolve() if args.output_text else None

    print(f"Input: {input_path}")
    print(f"Refiner base URL: {args.refiner_base_url}")
    print(f"Auth mode: {auth_mode(args, prefer_stt_token=True)}")
    if output_json:
        print(f"Transcript JSON: {output_json}")
    if output_text:
        print(f"Transcript text: {output_text}")
    sys.stdout.flush()

    if args.print_only:
        return 0

    client = build_client(args, prefer_stt_token=True)
    mime_type = mimetypes.guess_type(str(input_path))[0] or "application/octet-stream"
    fields = {
        "lang": args.lang,
        "prompt_hint": args.prompt_hint,
        "motionStyle": args.motion_style,
        "avatarMode": args.avatar_mode,
        "collaborationMode": "true" if args.collaboration_mode else None,
    }
    result = client.request_multipart(
        "POST",
        "/api/voice/stt",
        fields=fields,
        files=[("audio", input_path.name, input_path.read_bytes(), mime_type)],
        include_access_token=bool(client.access_token),
    )

    if output_json:
        write_json(output_json, result)
    if output_text:
        write_text(output_text, str(result.get("text") or ""))
    if not output_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def add_auth_arguments(parser: argparse.ArgumentParser, *, include_stt_token: bool = False) -> None:
    parser.add_argument("--refiner-base-url", default=DEFAULT_REFINER_BASE_URL)
    parser.add_argument(
        "--refiner-access-token",
        default=os.environ.get("REFINER_ACCESS_TOKEN") or os.environ.get("REFINER_API_TOKEN"),
    )
    parser.add_argument("--cookie-jar", default=os.environ.get("REFINER_COOKIE_JAR"))
    parser.add_argument("--username", default=os.environ.get("REFINER_USERNAME"))
    parser.add_argument("--password", default=os.environ.get("REFINER_PASSWORD"))
    parser.add_argument("--http-timeout", type=float, default=DEFAULT_HTTP_TIMEOUT)
    if include_stt_token:
        parser.add_argument("--stt-token", default=os.environ.get("REFINER_STT_TOKEN"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Refiner-managed marketing video workflows")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List the available product and training draft targets")

    draft = subparsers.add_parser("draft", help="Submit or preview a Refiner topic-research job")
    draft.add_argument("product", help="Product slug, for example refiner or tracey")
    draft.add_argument("--kind", choices=["product", "training"], default="product")
    draft.add_argument("--context-extra", action="append", default=[])
    draft.add_argument("--llm-provider")
    draft.add_argument("--llm-model")
    draft.add_argument("--llm-reasoning-effort")
    draft.add_argument("--max-iterations", type=int, default=6)
    draft.add_argument("--token-scope", choices=["personal", "team"])
    draft.add_argument("--team-id")
    draft.add_argument("--refiner-dry-run", action="store_true")
    draft.add_argument(
        "--allow-live-discovery",
        action="store_true",
        help="Allow Refiner topic research to query configured Jira/Confluence sources",
    )
    draft.add_argument("--print-only", action="store_true")
    draft.add_argument("--wait", dest="wait", action="store_true", default=True)
    draft.add_argument("--no-wait", dest="wait", action="store_false")
    draft.add_argument("--poll-interval", type=float, default=3.0)
    draft.add_argument("--wait-timeout", type=float)
    add_auth_arguments(draft)

    transcribe = subparsers.add_parser("transcribe", help="Transcribe recorded media through Refiner STT")
    transcribe.add_argument("input_file")
    transcribe.add_argument("output_json", nargs="?")
    transcribe.add_argument("--output-text")
    transcribe.add_argument("--lang", default="en-GB")
    transcribe.add_argument("--prompt-hint")
    transcribe.add_argument("--motion-style")
    transcribe.add_argument("--avatar-mode")
    transcribe.add_argument("--collaboration-mode", action="store_true")
    transcribe.add_argument("--print-only", action="store_true")
    add_auth_arguments(transcribe, include_stt_token=True)

    return parser


def format_api_error(exc: RefinerAPIError) -> str:
    details = exc.body.strip()
    try:
        payload = json.loads(details)
    except Exception:
        payload = None
    if isinstance(payload, dict):
        message = payload.get("details") or payload.get("error") or details
    else:
        message = details[:240] if details else ""
    if exc.status == 401:
        hint = " Authenticate with --username/--password, --cookie-jar, or --refiner-access-token."
    else:
        hint = ""
    if message:
        return f"Refiner API error ({exc.status}): {message}.{hint}".strip()
    return f"Refiner API error ({exc.status}).{hint}".strip()


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "list":
            return list_targets()
        if args.command == "draft":
            return draft_video(args)
        if args.command == "transcribe":
            return transcribe_media(args)
    except (FileNotFoundError, KeyError, RuntimeError, TimeoutError, RefinerAPIError) as exc:
        message = format_api_error(exc) if isinstance(exc, RefinerAPIError) else str(exc)
        print(message, file=sys.stderr)
        return 1
    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
