"""ByteTrack tracking via Ultralytics."""

from inference.detector import get_helmet_model


def track_video(video_path: str):
    """Yield per-frame tracking results from helmet model + ByteTrack."""
    model = get_helmet_model()
    return model.track(
        source=video_path,
        tracker="bytetrack.yaml",
        persist=True,
        stream=True,
        verbose=False,
    )
