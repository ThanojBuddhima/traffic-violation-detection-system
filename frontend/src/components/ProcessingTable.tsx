import { useState } from "react";
import type { Video } from "../api/client";
import { VideoReviewModal } from "./VideoReviewModal";

interface Props {
  videos: Video[];
}

const statusClass = (status: string) => {
  switch (status) {
    case "done":
      return "status-done";
    case "failed":
      return "status-failed";
    case "processing":
      return "status-processing";
    default:
      return "status-queued";
  }
};

export function ProcessingTable({ videos }: Props) {
  const [reviewVideo, setReviewVideo] = useState<Video | null>(null);

  if (videos.length === 0) {
    return <p className="empty">No uploads yet.</p>;
  }

  return (
    <>
      <table className="data-table">
        <thead>
          <tr>
            <th>Filename</th>
            <th>Status</th>
            <th>Uploaded</th>
            <th>Processed</th>
            <th>Error</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {videos.map((v) => (
            <tr key={v.id}>
              <td>{v.filename}</td>
              <td>
                <span className={`badge ${statusClass(v.status)}`}>{v.status}</span>
              </td>
              <td>{new Date(v.upload_time).toLocaleString()}</td>
              <td>{v.processed_at ? new Date(v.processed_at).toLocaleString() : "—"}</td>
              <td className="error-cell">{v.error_message || "—"}</td>
              <td>
                {v.status === "done" && (
                  <button type="button" className="btn-sm" onClick={() => setReviewVideo(v)}>
                    Review
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {reviewVideo && (
        <VideoReviewModal video={reviewVideo} onClose={() => setReviewVideo(null)} />
      )}
    </>
  );
}
