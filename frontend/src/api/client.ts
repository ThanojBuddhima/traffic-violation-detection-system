import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({ baseURL: API_URL });

export function uploadErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((item) => item.msg ?? String(item)).join("; ");
    }
    return error.message;
  }
  return error instanceof Error ? error.message : "Upload failed";
}

export interface Video {
  id: string;
  filename: string;
  status: string;
  upload_time: string;
  duration_seconds: number | null;
  width: number | null;
  height: number | null;
  processed_at: string | null;
  error_message: string | null;
}

export interface OverlayFrame {
  t: number;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface Violation {
  id: number;
  video_id: string;
  track_id: number;
  plate_number: string;
  plate_confidence: number;
  helmet_confidence: number;
  frame_timestamp: number;
  evidence_image_path: string;
  plate_image_path: string | null;
  overlay_frames: OverlayFrame[];
  created_at: string;
  reviewed: boolean;
}

export interface Health {
  status: string;
  storage_backend: string;
  use_celery: boolean;
  use_mock_models: boolean;
  database_dialect: string;
}

export async function fetchHealth(): Promise<Health> {
  const { data } = await api.get<Health>("/api/health");
  return data;
}

export async function fetchVideos(): Promise<Video[]> {
  const { data } = await api.get<Video[]>("/api/videos");
  return data;
}

export async function uploadVideo(file: File): Promise<{ video_id: string; status: string }> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/api/videos/upload", form);
  return data;
}

export async function fetchViolations(params?: {
  plate?: string;
  video_id?: string;
  reviewed?: boolean;
}): Promise<Violation[]> {
  const { data } = await api.get<Violation[]>("/api/violations", { params });
  return data;
}

export async function deleteViolation(id: number): Promise<void> {
  await api.delete(`/api/violations/${id}`);
}

export async function updateViolation(
  id: number,
  body: { plate_number?: string; reviewed?: boolean }
): Promise<Violation> {
  const { data } = await api.patch<Violation>(`/api/violations/${id}`, body);
  return data;
}

export function violationImageUrl(id: number): string {
  return `${API_URL}/api/violations/${id}/image`;
}

export function violationPlateImageUrl(id: number): string {
  return `${API_URL}/api/violations/${id}/plate-image`;
}

export function videoStreamUrl(id: string): string {
  return `${API_URL}/api/videos/${id}/stream`;
}

const IMAGE_EXT = /\.(jpe?g|png|webp|bmp|heic|heif|jfif|tiff?)$/i;

export function isImageFilename(filename: string): boolean {
  return IMAGE_EXT.test(filename);
}
