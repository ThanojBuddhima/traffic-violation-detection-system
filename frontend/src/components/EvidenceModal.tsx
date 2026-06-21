import { useState } from "react";
import type { Violation } from "../api/client";
import { updateViolation, violationImageUrl, violationPlateImageUrl } from "../api/client";

interface Props {
  violation: Violation;
  onClose: () => void;
  onChange: () => void;
}

export function EvidenceModal({ violation, onClose, onChange }: Props) {
  const [plate, setPlate] = useState(violation.plate_number);
  const [saving, setSaving] = useState(false);
  const [plateImageError, setPlateImageError] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateViolation(violation.id, { plate_number: plate, reviewed: true });
      onChange();
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>
          ×
        </button>
        <h2>Violation #{violation.id}</h2>
        <div className="evidence-dual">
          <figure>
            <figcaption>Rider evidence</figcaption>
            <img
              src={violationImageUrl(violation.id)}
              alt="Rider evidence"
              className="evidence-full"
            />
          </figure>
          {violation.plate_image_path && !plateImageError && (
            <figure>
              <figcaption>Plate crop</figcaption>
              <img
                src={violationPlateImageUrl(violation.id)}
                alt="Plate crop"
                className="evidence-full"
                onError={() => setPlateImageError(true)}
              />
            </figure>
          )}
        </div>
        <div className="modal-meta">
          <p>
            <strong>Track ID:</strong> {violation.track_id}
          </p>
          <p>
            <strong>Timestamp:</strong> {violation.frame_timestamp.toFixed(2)}s
          </p>
          <p>
            <strong>Helmet confidence:</strong> {(violation.helmet_confidence * 100).toFixed(1)}%
          </p>
          <p>
            <strong>OCR confidence:</strong> {(violation.plate_confidence * 100).toFixed(1)}%
          </p>
          <p>
            <strong>Video ID:</strong> {violation.video_id}
          </p>
        </div>
        <label className="plate-edit">
          Plate number
          <input value={plate} onChange={(e) => setPlate(e.target.value)} />
        </label>
        <button className="btn-primary" onClick={handleSave} disabled={saving}>
          {saving ? "Saving…" : "Save & mark reviewed"}
        </button>
      </div>
    </div>
  );
}
