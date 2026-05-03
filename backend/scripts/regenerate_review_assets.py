from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


BASE_URL = "http://localhost:4000"
LOG_PATH = Path(__file__).resolve().parents[1] / "review-asset-regeneration.log"
CONTENT_IDS = [
    "content_showcase_learning-clock_record",
    "content_showcase_learning-fraction_record",
    "content_showcase_life-bus_record",
]


def log(message: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {message}"
    print(line, flush=True)
    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(line + "\n")


def request_json(method: str, path: str, payload: dict[str, Any] | None = None, timeout: int = 900) -> Any:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            text = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} failed: {exc.code} {detail}") from exc
    parsed = json.loads(text) if text else {}
    if "error" in parsed or "detail" in parsed:
        raise RuntimeError(f"{method} {path} failed: {parsed}")
    return parsed.get("data")


def main() -> None:
    if LOG_PATH.exists():
        LOG_PATH.unlink()
    log("review asset regeneration started")
    for content_id in CONTENT_IDS:
        content = request_json("GET", f"/api/contents/{content_id}", timeout=60)
        assets = sorted(content["assets"], key=lambda item: (item["assetType"], item["assetRole"], item["id"]))
        log(f"{content_id}: {len(assets)} assets queued")
        for index, asset in enumerate(assets, start=1):
            log(f"{content_id}: generating {index}/{len(assets)} {asset['id']}")
            generated = request_json("POST", f"/api/contents/{content_id}/assets/{asset['id']}/generate", timeout=900)
            log(f"{content_id}: ready {generated['id']} {generated.get('previewUrl') or generated.get('storageUrl')}")
    log("review asset regeneration completed")


if __name__ == "__main__":
    main()
