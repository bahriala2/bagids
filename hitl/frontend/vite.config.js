import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Le backend HITL (FastAPI) tourne sur :8090. En développement, Vite
// proxifie /api et /ws vers lui ; en production, FastAPI sert dist/.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5175,
    proxy: {
      "/api": { target: "http://127.0.0.1:8090", changeOrigin: true },
      "/ws": { target: "ws://127.0.0.1:8090", ws: true },
    },
  },
  build: { outDir: "dist", emptyOutDir: true },
});
