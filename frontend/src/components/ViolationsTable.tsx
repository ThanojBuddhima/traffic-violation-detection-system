import { useState } from "react";
import type { Violation } from "../api/client";
import { deleteViolation, updateViolation, violationImageUrl } from "../api/client";
import { EvidenceModal } from "./EvidenceModal";

interface Props {
  violations: Violation[];
  onChange: () => void;
}

function confidenceBadge(conf: number) {
  if (conf < 0.6) return "conf-low";
  if (conf < 0.8) return "conf-medium";
  return "conf-high";
}

export function ViolationsTable({ violations, onChange }: Props) {
  const [selected, setSelected] = useState<Violation | null>(null);

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this violation?")) return;
    await deleteViolation(id);
    onChange();
  };

  const handleReview = async (v: Violation) => {
    await updateViolation(v.id, { reviewed: true });
    onChange();
  };

  if (violations.length === 0) {
    return <p className="empty">No violations detected yet.</p>;
  }

  return (
    <>
      <table className="data-table">
        <thead>
          <tr>
            <th>Thumbnail</th>
            <th>Plate</th>
            <th>Timestamp</th>
            <th>Helmet conf.</th>
            <th>OCR conf.</th>
            <th>Reviewed</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {violations.map((v) => (
            <tr key={v.id} onClick={() => setSelected(v)} className="clickable-row">
              <td>
                <img
                  src={violationImageUrl(v.id)}
                  alt={`Evidence ${v.id}`}
                  className="thumb"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = "none";
                  }}
                />
              </td>
              <td>{v.plate_number}</td>
              <td>{v.frame_timestamp.toFixed(1)}s</td>
              <td>
                <span className={`badge ${confidenceBadge(v.helmet_confidence)}`}>
                  {(v.helmet_confidence * 100).toFixed(0)}%
                </span>
              </td>
              <td>
                <span className={`badge ${confidenceBadge(v.plate_confidence)}`}>
                  {(v.plate_confidence * 100).toFixed(0)}%
                </span>
              </td>
              <td>{v.reviewed ? "Yes" : "No"}</td>
              <td onClick={(e) => e.stopPropagation()}>
                {!v.reviewed && (
                  <button className="btn-sm" onClick={() => handleReview(v)}>
                    Mark reviewed
                  </button>
                )}
                <button className="btn-sm btn-danger" onClick={() => handleDelete(v.id)}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {selected && (
        <EvidenceModal violation={selected} onClose={() => setSelected(null)} onChange={onChange} />
      )}
    </>
  );
}
