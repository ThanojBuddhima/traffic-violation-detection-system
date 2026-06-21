#!/usr/bin/env python3
"""End-to-end API smoke test (mock mode)."""

import io
import sys
import time

import httpx

BASE = "http://localhost:8000"


def main():
    with httpx.Client(base_url=BASE, timeout=30) as client:
        health = client.get("/api/health").json()
        assert health["status"] == "ok", health
        assert health["use_mock_models"] is True, "Expected mock mode for smoke test"
        print("Health OK:", health)

        fake_video = io.BytesIO(b"\x00" * 10240)
        files = {"file": ("smoke_test.mp4", fake_video, "video/mp4")}
        upload = client.post("/api/videos/upload", files=files).json()
        video_id = upload["video_id"]
        print("Uploaded:", video_id)

        for _ in range(20):
            status = client.get(f"/api/videos/{video_id}/status").json()
            if status["status"] in ("done", "failed"):
                break
            time.sleep(0.5)

        assert status["status"] == "done", f"Expected done, got {status}"
        print("Processing done")

        violations = client.get("/api/violations", params={"video_id": video_id}).json()
        assert len(violations) >= 1, "Expected at least one violation"
        print(f"Violations: {len(violations)}")

        img = client.get(f"/api/violations/{violations[0]['id']}/image")
        assert img.status_code == 200 and img.headers["content-type"] == "image/jpeg"
        print("Evidence image OK")

    print("All smoke tests passed")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)
