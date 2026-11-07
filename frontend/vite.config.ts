import { defineConfig, loadEnv, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";
import { createApiProxy } from "./server/proxy-core.mjs";

/**
 * Same-origin auth proxy for dev and `vite preview`.
 * The API key is read from DOCUMIND_PROXY_API_KEY (no VITE_ prefix), so it is
 * only available to this Node process and is never bundled into browser code.
 */
function documindProxy(mode: string): Plugin {
  const env = loadEnv(mode, process.cwd(), "DOCUMIND_");
  const handler = createApiProxy({
    backendUrl: env.DOCUMIND_BACKEND_URL || "http://127.0.0.1:8001",
    apiKey: env.DOCUMIND_PROXY_API_KEY || "",
  });
  return {
    name: "documind-auth-proxy",
    configureServer(server) {
      server.middlewares.use(handler);
    },
    configurePreviewServer(server) {
      server.middlewares.use(handler);
    },
  };
}

export default defineConfig(({ mode }) => ({
  plugins: [react(), documindProxy(mode)],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
}));
