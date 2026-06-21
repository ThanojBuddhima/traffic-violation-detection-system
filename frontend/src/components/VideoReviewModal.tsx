import { useCallback, useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import type { OverlayFrame, Video, Violation } from "../api/client";
import { fetchViolations, isImageFilename, videoStreamUrl } from "../api/client";

interface Props {
  video: Video;
  onClose: () => void;
}

const OVERLAY_TOLERANCE = 0.05;

function framesAtTime(frames: OverlayFrame[], t: number): OverlayFrame[] {
  return frames.filter((f) => Math.abs(f.t - t) <= OVERLAY_TOLERANCE);
}

export function VideoReviewModal({ video, onClose }: Props) {
  const mediaRef = useRef<HTMLVideoElement | HTMLImageElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [activeViolationId, setActiveViolationId] = useState<number | null>(null);
  const isImage = isImageFilename(video.filename);

  const { data: violations = [], isLoading } = useQuery({
    queryKey: ["violations", video.id],
    queryFn: () => fetchViolations({ video_id: video.id }),
  });

  const sourceWidth = video.width ?? 0;
  const sourceHeight = video.height ?? 0;

  const drawOverlays = useCallback(
    (time: number) => {
      const canvas = canvasRef.current;
      const wrapper = wrapperRef.current;
      const media = mediaRef.current;
      if (!canvas || !wrapper || !media) return;

      const displayWidth = media.clientWidth;
      const displayHeight = media.clientHeight;
      if (!displayWidth || !displayHeight) return;

      canvas.width = displayWidth;
      canvas.height = displayHeight;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      ctx.clearRect(0, 0, displayWidth, displayHeight);

      const vidW =
        !isImage && media instanceof HTMLVideoElement
          ? media.videoWidth || sourceWidth
          : sourceWidth || (media instanceof HTMLImageElement ? media.naturalWidth : 0);
      const vidH =
        !isImage && media instanceof HTMLVideoElement
          ? media.videoHeight || sourceHeight
          : sourceHeight || (media instanceof HTMLImageElement ? media.naturalHeight : 0);

      if (!vidW || !vidH) return;

      const scaleX = displayWidth / vidW;
      const scaleY = displayHeight / vidH;

      let activeId: number | null = null;
      for (const v of violations) {
        const frames = isImage ? v.overlay_frames : framesAtTime(v.overlay_frames, time);
        for (const frame of frames) {
          activeId = v.id;
          const x = frame.x1 * scaleX;
          const y = frame.y1 * scaleY;
          const w = (frame.x2 - frame.x1) * scaleX;
          const h = (frame.y2 - frame.y1) * scaleY;

          ctx.strokeStyle = "#ff0000";
          ctx.lineWidth = 3;
          ctx.strokeRect(x, y, w, h);

          const label = v.plate_number !== "UNKNOWN" ? v.plate_number : `Track ${v.track_id}`;
          ctx.font = "bold 14px system-ui, sans-serif";
          const textW = ctx.measureText(label).width;
          ctx.fillStyle = "rgba(255, 0, 0, 0.85)";
          ctx.fillRect(x, Math.max(0, y - 20), textW + 8, 20);
          ctx.fillStyle = "#fff";
          ctx.fillText(label, x + 4, Math.max(14, y - 6));
        }
      }
      setActiveViolationId(activeId);
    },
    [violations, isImage, sourceWidth, sourceHeight]
  );

  useEffect(() => {
    drawOverlays(currentTime);
  }, [currentTime, drawOverlays, violations]);

  useEffect(() => {
    const onResize = () => drawOverlays(currentTime);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [currentTime, drawOverlays]);

  useEffect(() => {
    if (isImage) {
      drawOverlays(0);
    }
  }, [isImage, drawOverlays]);

  const seekToViolation = (v: Violation) => {
    if (isImage) return;
    const el = mediaRef.current;
    if (el instanceof HTMLVideoElement) {
      el.currentTime = v.frame_timestamp;
      setCurrentTime(v.frame_timestamp);
    }
  };

  const streamUrl = videoStreamUrl(video.id);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-wide" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>
          ×
        </button>
        <h2>Review: {video.filename}</h2>

        <div className="video-review-container">
          <div className="video-canvas-wrapper" ref={wrapperRef}>
            {isImage ? (
              <img
                ref={mediaRef as React.RefObject<HTMLImageElement>}
                src={streamUrl}
                alt={video.filename}
                className="review-media"
                onLoad={() => drawOverlays(0)}
              />
            ) : (
              <video
                ref={mediaRef as React.RefObject<HTMLVideoElement>}
                src={streamUrl}
                className="review-media"
                controls
                onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
                onLoadedMetadata={(e) => {
                  setCurrentTime(e.currentTarget.currentTime);
                  drawOverlays(e.currentTarget.currentTime);
                }}
              />
            )}
            <canvas ref={canvasRef} className="review-canvas" />
          </div>

          <aside className="review-sidebar">
            <h3>Violations ({violations.length})</h3>
            {isLoading ? (
              <p>Loading…</p>
            ) : violations.length === 0 ? (
              <p className="empty">No violations for this upload.</p>
            ) : (
              <ul className="review-violation-list">
                {violations.map((v) => (
                  <li key={v.id}>
                    <button
                      type="button"
                      className={`review-violation-item${activeViolationId === v.id ? " active" : ""}`}
                      onClick={() => seekToViolation(v)}
                    >
                      <strong>{v.plate_number}</strong>
                      <span>Track {v.track_id}</span>
                      {!isImage && <span>{v.frame_timestamp.toFixed(1)}s</span>}
                      <span>{(v.helmet_confidence * 100).toFixed(0)}% helmet</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </aside>
        </div>
      </div>
    </div>
  );
}
