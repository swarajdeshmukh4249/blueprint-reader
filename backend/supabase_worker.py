import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from blueprint_logic import analyze_blueprint

try:
    import certifi
except ImportError:
    certifi = None


DEFAULT_POLL_INTERVAL = 5
JOB_COLUMNS = "id,file_name,file_path,file_type,storage_bucket,status,result,error,created_at,updated_at"


def build_ssl_context() -> ssl.SSLContext:
    if certifi is not None:
        return ssl.create_default_context(cafile=certifi.where())
    return ssl.create_default_context()


def load_env_file(path: str) -> None:
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key and key not in os.environ:
                os.environ[key] = value


def get_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def build_headers(api_key: str, extra_headers: dict[str, str] | None = None) -> dict[str, str]:
    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
    }
    if extra_headers:
        headers.update(extra_headers)
    return headers


def make_request(
    url: str,
    api_key: str,
    method: str = "GET",
    body: bytes | None = None,
    extra_headers: dict[str, str] | None = None,
) -> Any:
    headers = build_headers(api_key, extra_headers)
    request = urllib.request.Request(url=url, data=body, headers=headers, method=method)
    ssl_context = build_ssl_context()

    try:
        with urllib.request.urlopen(request, timeout=60, context=ssl_context) as response:
            raw = response.read()
            if not raw:
                return None
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed with {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{method} {url} failed: {exc.reason}") from exc


def fetch_next_job(project_url: str, service_role_key: str) -> dict[str, Any] | None:
    query = urllib.parse.urlencode(
        {
            "select": JOB_COLUMNS,
            "status": "eq.queued",
            "order": "created_at.asc",
            "limit": "1",
        }
    )
    url = f"{project_url}/rest/v1/analysis_jobs?{query}"
    jobs = make_request(
        url,
        service_role_key,
        extra_headers={
            "Prefer": "return=representation",
            "Content-Type": "application/json",
        },
    )

    if not jobs:
        return None

    return jobs[0]


def update_job(
    project_url: str,
    service_role_key: str,
    job_id: str,
    payload: dict[str, Any],
) -> None:
    query = urllib.parse.urlencode({"id": f"eq.{job_id}"})
    url = f"{project_url}/rest/v1/analysis_jobs?{query}"
    make_request(
        url,
        service_role_key,
        method="PATCH",
        body=json.dumps(payload).encode("utf-8"),
        extra_headers={
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
    )


def download_file(project_url: str, service_role_key: str, bucket: str, file_path: str) -> bytes:
    encoded_path = urllib.parse.quote(file_path, safe="/")
    url = f"{project_url}/storage/v1/object/{bucket}/{encoded_path}"
    request = urllib.request.Request(
        url=url,
        headers=build_headers(service_role_key),
        method="GET",
    )
    ssl_context = build_ssl_context()

    try:
        with urllib.request.urlopen(request, timeout=120, context=ssl_context) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Download failed with {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Download failed: {exc.reason}") from exc


def process_job(project_url: str, service_role_key: str, job: dict[str, Any]) -> None:
    job_id = str(job["id"])
    bucket = str(job.get("storage_bucket") or "blueprints")
    file_path = str(job["file_path"])
    file_name = str(job["file_name"])

    print(f"Processing job {job_id} for {file_name}", flush=True)

    update_job(
        project_url,
        service_role_key,
        job_id,
        {
            "status": "processing",
            "error": None,
        },
    )

    try:
        file_bytes = download_file(project_url, service_role_key, bucket, file_path)
        result = analyze_blueprint(file_bytes, file_name)

        if result.get("error"):
            update_job(
                project_url,
                service_role_key,
                job_id,
                {
                    "status": "failed",
                    "result": result,
                    "error": result.get("error"),
                },
            )
            print(f"Failed job {job_id}: {result.get('error')}", file=sys.stderr, flush=True)
            return

        quality = result.get("extraction_quality") or {}
        rooms_with_area = quality.get("rooms_with_area", 0)
        if rooms_with_area == 0:
            update_job(
                project_url,
                service_role_key,
                job_id,
                {
                    "status": "completed",
                    "result": result,
                    "error": (
                        "Analysis completed but no room areas were detected. "
                        "Upload a clearer file or set GOOGLE_API_KEY on Railway."
                    ),
                },
            )
            print(f"Completed job {job_id} with warnings (no areas)", flush=True)
            return

        update_job(
            project_url,
            service_role_key,
            job_id,
            {
                "status": "completed",
                "result": result,
                "error": None,
            },
        )
        print(f"Completed job {job_id}", flush=True)
    except Exception as exc:
        update_job(
            project_url,
            service_role_key,
            job_id,
            {
                "status": "failed",
                "error": str(exc),
            },
        )
        print(f"Failed job {job_id}: {exc}", file=sys.stderr, flush=True)


def main() -> int:
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    load_env_file(os.path.join(backend_dir, ".env"))

    project_url = get_env("SUPABASE_URL").rstrip("/")
    service_role_key = get_env("SUPABASE_SERVICE_ROLE_KEY")
    poll_interval = int(os.environ.get("SUPABASE_POLL_INTERVAL", DEFAULT_POLL_INTERVAL))

    print("Supabase worker started", flush=True)

    while True:
        try:
            job = fetch_next_job(project_url, service_role_key)
            if not job:
                time.sleep(poll_interval)
                continue

            process_job(project_url, service_role_key, job)
        except KeyboardInterrupt:
            print("Worker stopped", flush=True)
            return 0
        except Exception as exc:
            print(f"Worker loop error: {exc}", file=sys.stderr, flush=True)
            time.sleep(poll_interval)


if __name__ == "__main__":
    raise SystemExit(main())