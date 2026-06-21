import { useCallback, useState } from "react";
import { uploadVideo, uploadErrorMessage } from "../api/client";

const ALLOWED_EXT = /\.(mp4|avi|mov|mkv|webm|m4v|mpeg|mpg|3gp|jpe?g|jfif|png|webp|bmp|heic|heif|tiff?)$/i;

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
        setError("Please upload a video (.mp4, .mov, .m4v) or image (.jpg, .png, .heic, .webp)");
        return;
      }
      setError(null);
      setUploading(true);
      try {
        await uploadVideo(file);
        onUploaded();
      } catch (e: unknown) {
        setError(uploadErrorMessage(e));
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
          accept="video/*,image/*,.mp4,.avi,.mov,.mkv,.m4v,.jpg,.jpeg,.png,.webp,.bmp,.heic,.heif,.jfif"
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
