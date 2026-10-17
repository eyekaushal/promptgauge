import { useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes } from "react-router";

import { ApiClient } from "./api/ApiClient.js";
import Ablation from "./screens/Ablation.jsx";
import Datasets from "./screens/Datasets.jsx";
import Experiments from "./screens/Experiments.jsx";
import Settings from "./screens/Settings.jsx";
import Sidebar from "./ui/Sidebar.jsx";

/** The shell: sidebar, one panel for the screen, the API client built once (DESIGN.md §6). */
export default function App() {
  const api = useMemo(() => new ApiClient(), []);
  const [health, setHealth] = useState({ data: null, error: null });

  useEffect(() => {
    let alive = true;
    api
      .health()
      .then((data) => alive && setHealth({ data, error: null }))
      .catch((error) => alive && setHealth({ data: null, error }));
    return () => {
      alive = false;
    };
  }, [api]);

  return (
    <div className="flex h-full min-w-[720px]">
      <Sidebar health={health} />
      <main className="min-w-0 flex-1 p-4">
        <div className="flex h-full min-h-0 flex-col rounded-lg border border-line bg-panel">
          <Routes>
            <Route path="/" element={<Navigate to="/experiments" replace />} />
            <Route path="/datasets" element={<Datasets api={api} />} />
            <Route path="/experiments" element={<Experiments api={api} />} />
            <Route path="/experiments/:id" element={<Experiments api={api} />} />
            <Route path="/ablations" element={<Ablation api={api} />} />
            <Route path="/ablations/:id" element={<Ablation api={api} />} />
            <Route path="/settings" element={<Settings api={api} />} />
            <Route path="*" element={<Navigate to="/experiments" replace />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
