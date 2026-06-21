-- Reference DDL (idea.md §H). V1 uses SQLAlchemy create_all(); V2 uses Alembic against Postgres.

CREATE TABLE videos (
    id VARCHAR(36) PRIMARY KEY,
    filename VARCHAR(512) NOT NULL,
    storage_key VARCHAR(1024) NOT NULL,
    upload_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(32) NOT NULL,
    duration_seconds FLOAT,
    width INTEGER,
    height INTEGER,
    processed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT
);

CREATE TABLE violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id VARCHAR(36) NOT NULL REFERENCES videos(id),
    track_id INTEGER NOT NULL,
    plate_number VARCHAR(64) NOT NULL,
    plate_confidence FLOAT DEFAULT 0.0,
    helmet_confidence FLOAT DEFAULT 0.0,
    frame_timestamp FLOAT DEFAULT 0.0,
    evidence_image_path VARCHAR(1024) NOT NULL,
    plate_image_path VARCHAR(1024),
    overlay_frames TEXT DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE,
    reviewed BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_plate ON violations(plate_number);
CREATE INDEX idx_video ON violations(video_id);
