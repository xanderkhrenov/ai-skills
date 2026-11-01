import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { Health } from "./api/generated/Health";
import "./style.css";

const api = new Health({ baseUrl: "" });

function App() {
  const [status, setStatus] = useState("Проверяем backend…");
  useEffect(() => {
    let active = true;
    api.checkHealth()
      .then(({ data }) => { if (active) setStatus(data.status === "serving" ? "Backend доступен" : "Backend не готов"); })
      .catch(() => { if (active) setStatus("Backend недоступен — проверьте его запуск"); });
    return () => { active = false; };
  }, []);
  return <main><p className="eyebrow">Стартовый каркас</p><h1>__PROJECT_NAME__</h1><p role="status">{status}</p><p>React · HTTP gateway · gRPC</p></main>;
}

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
