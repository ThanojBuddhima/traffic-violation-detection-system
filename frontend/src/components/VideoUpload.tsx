import { useCallback, useState } from "react";
import { uploadVideo } from "../api/client";

interface Props {
  onUploaded: () => void;
}

export function VideoUpload({ onUploaded }: Props) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.type.startsWith("video/") && !file.name.match(/\.(mp4|avi|mov|mkv)$/i)) {
        setError("Please upload a video file (.mp4, .avi, .mov, .mkv)");
        return;
      }
      setError(null);
      setUploading(true);
      try {
        await uploadVideo(file);
        onUploaded();
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Upload failed");
      } finally {
        setUploading(false);
      }
    },
    [onUploaded]
  );

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  return (
    <div
      className={`upload-zone ${dragging ? "dragging" : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
    >
      <p>{uploading ? "Uploading…" : "Drag & drop a traffic video here"}</p>
      <label className="upload-btn">
        {uploading ? "Processing upload…" : "Browse files"}
        <input
          type="file"
          accept="video/*,.mp4,.avi,.mov,.mkv"
          hidden
          disabled={uploading}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
        />
      </label>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
