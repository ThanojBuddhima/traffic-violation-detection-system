import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { fetchHealth, fetchVideos, fetchViolations } from "./api/client";
import { ProcessingTable } from "./components/ProcessingTable";
import { VideoUpload } from "./components/VideoUpload";
import { ViolationsTable } from "./components/ViolationsTable";
import "./App.css";

function App() {
  const [plateFilter, setPlateFilter] = useState("");
  const [reviewedFilter, setReviewedFilter] = useState<string>("");

  const health = useQuery({ queryKey: ["health"], queryFn: fetchHealth, refetchInterval: 30000 });

  const videos = useQuery({
    queryKey: ["videos"],
    queryFn: fetchVideos,
    refetchInterval: (query) => {
      const data = query.state.data;
      const active = data?.some((v) => v.status === "queued" || v.status === "processing");
      return active ? 2500 : false;
    },
  });

  const violations = useQuery({
    queryKey: ["violations", plateFilter, reviewedFilter],
    queryFn: () =>
      fetchViolations({
        plate: plateFilter || undefined,
        reviewed: reviewedFilter === "" ? undefined : reviewedFilter === "true",
      }),
    refetchInterval: () => {
      const vids = videos.data;
      const active = vids?.some((v) => v.status === "queued" || v.status === "processing");
      return active ? 2500 : false;
    },
  });

  const refresh = () => {
    videos.refetch();
    violations.refetch();
  };

  return (
    <div className="app">
      <header>
        <h1>Helmet Violation Detection</h1>
        <p className="subtitle">Sri Lankan traffic video and image analysis</p>
        {health.data && (
          <div className="health-banner">
            {health.data.use_mock_models && (
              <span className="banner-mock">Mock inference mode — upload works without trained models</span>
            )}
            <span className="banner-meta">
              Storage: {health.data.storage_backend} · DB: {health.data.database_dialect}
              {health.data.use_celery && " · Celery"}
            </span>
          </div>
        )}
      </header>

      <main>
        <section>
          <h2>Upload Video</h2>
          <VideoUpload onUploaded={refresh} />
        </section>

        <section>
          <h2>Processing Status</h2>
          {videos.isLoading ? <p>Loading…</p> : <ProcessingTable videos={videos.data ?? []} />}
        </section>

        <section>
          <h2>Violations</h2>
          <div className="filters">
            <input
              placeholder="Filter by plate…"
              value={plateFilter}
              onChange={(e) => setPlateFilter(e.target.value)}
            />
            <select value={reviewedFilter} onChange={(e) => setReviewedFilter(e.target.value)}>
              <option value="">All</option>
              <option value="false">Unreviewed</option>
              <option value="true">Reviewed</option>
            </select>
          </div>
          {violations.isLoading ? (
            <p>Loading…</p>
          ) : (
            <ViolationsTable violations={violations.data ?? []} onChange={refresh} />
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
