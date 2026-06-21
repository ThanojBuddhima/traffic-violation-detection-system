import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({ baseURL: API_URL });

export interface Video {
  id: string;
  filename: string;
  status: string;
  upload_time: string;
  duration_seconds: number | null;
  processed_at: string | null;
  error_message: string | null;
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
  const { data } = await api.post("/api/videos/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
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
