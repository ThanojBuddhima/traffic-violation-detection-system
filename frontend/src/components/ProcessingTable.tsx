import type { Video } from "../api/client";

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
  if (videos.length === 0) {
    return <p className="empty">No videos uploaded yet.</p>;
  }

  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Filename</th>
          <th>Status</th>
          <th>Uploaded</th>
          <th>Processed</th>
          <th>Error</th>
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
          </tr>
        ))}
      </tbody>
    </table>
  );
}
