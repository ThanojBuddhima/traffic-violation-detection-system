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
        v0 = violations[0]
        assert isinstance(v0.get("overlay_frames"), list), "overlay_frames should be a list"
        assert len(v0["overlay_frames"]) >= 1, "Expected overlay frame data"
        print(f"Violations: {len(violations)}, overlay frames: {len(v0['overlay_frames'])}")

        img = client.get(f"/api/violations/{v0['id']}/image")
        assert img.status_code == 200 and img.headers["content-type"] == "image/jpeg"
        print("Evidence image OK")

        if v0.get("plate_image_path"):
            plate_img = client.get(f"/api/violations/{v0['id']}/plate-image")
            assert plate_img.status_code == 200 and plate_img.headers["content-type"] == "image/jpeg"
            print("Plate image OK")

        stream = client.get(f"/api/videos/{video_id}/stream")
        assert stream.status_code == 200, f"Stream failed: {stream.status_code}"
        print("Video stream OK")

    print("All smoke tests passed")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)
