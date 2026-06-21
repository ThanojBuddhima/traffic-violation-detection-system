import { useCallback, useState } from "react";
import { uploadVideo } from "../api/client";

const ALLOWED_EXT = /\.(mp4|avi|mov|mkv|webm|jpe?g|png|webp|bmp)$/i;

function isAllowedFile(file: File): boolean {
  return file.type.startsWith("video/") || file.type.startsWith("image/") || ALLOWED_EXT.test(file.name);
}

interface Props {
  onUploaded: () => void;
}

export function VideoUpload({ onUploaded }: Props) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      if (!isAllowedFile(file)) {
        setError("Please upload a video (.mp4, .avi, .mov, .mkv) or image (.jpg, .png, .webp, .bmp)");
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
      <p>{uploading ? "Uploading…" : "Drag & drop a traffic video or image here"}</p>
      <label className="upload-btn">
        {uploading ? "Processing upload…" : "Browse files"}
        <input
          type="file"
          accept="video/*,image/*,.mp4,.avi,.mov,.mkv,.jpg,.jpeg,.png,.webp,.bmp"
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
