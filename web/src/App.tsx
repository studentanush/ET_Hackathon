import { Routes, Route } from "react-router-dom";
import { useEffect, useState } from "react";
import Layout from "./components/Layout";
import { ToastHost } from "./components/ui";
import { apiGet } from "./lib/api";
import Dashboard from "./pages/Dashboard";
import Compliance from "./pages/Compliance";
import ScheduleRisk from "./pages/ScheduleRisk";
import SupplyChain from "./pages/SupplyChain";
import Commissioning from "./pages/Commissioning";
import Knowledge from "./pages/Knowledge";
import Graph from "./pages/Graph";
import Audit from "./pages/Audit";

export default function App() {
  const [project, setProject] = useState<any>(null);
  useEffect(() => {
    apiGet("/dashboard")
      .then((d) => setProject(d.project))
      .catch(() => {});
  }, []);

  return (
    <ToastHost>
      <Layout project={project}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/compliance" element={<Compliance />} />
          <Route path="/schedule" element={<ScheduleRisk />} />
          <Route path="/supply" element={<SupplyChain />} />
          <Route path="/commissioning" element={<Commissioning />} />
          <Route path="/knowledge" element={<Knowledge />} />
          <Route path="/graph" element={<Graph />} />
          <Route path="/audit" element={<Audit />} />
        </Routes>
      </Layout>
    </ToastHost>
  );
}
