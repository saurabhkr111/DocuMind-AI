// Production server: serves the built SPA from ../dist and proxies the API with
// server-side authentication. Run with `npm run build && npm start`.
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createApiProxy } from "./proxy-core.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const dist = path.join(root, "dist");

// Minimal .env loader (process.env always wins). Only DOCUMIND_*, PORT, HOST are read.
function loadEnvFile(file) {
  if (!fs.existsSync(file)) return;
  for (const line of fs.readFileSync(file, "utf8").split(/\r?\n/)) {
    const m = line.match(/^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*)\s*$/);
    if (!m || line.trim().startsWith("#")) continue;
    const [, key, raw] = m;
    if (!(key.startsWith("DOCUMIND_") || key === "PORT" || key === "HOST")) continue;
    if (process.env[key] === undefined) process.env[key] = raw.replace(/^['"]|['"]$/g, "");
  }
}
loadEnvFile(path.join(root, ".env.local"));
loadEnvFile(path.join(root, ".env"));

const port = Number(process.env.PORT || 5173);
const host = process.env.HOST || "127.0.0.1";

const proxy = createApiProxy({
  backendUrl: process.env.DOCUMIND_BACKEND_URL || "http://127.0.0.1:8001",
  apiKey: process.env.DOCUMIND_PROXY_API_KEY || "",
});

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".svg": "image/svg+xml",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".ico": "image/x-icon",
  ".woff2": "font/woff2",
  ".map": "application/json",
};

const SECURITY_HEADERS = {
  "Content-Security-Policy":
    "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "no-referrer",
  "X-Frame-Options": "DENY",
};

function serveStatic(req, res) {
  if (!fs.existsSync(dist)) {
    res.statusCode = 500;
    res.end("Build not found. Run `npm run build` first.");
    return;
  }
  const { pathname } = new URL(req.url || "/", "http://localhost");
  let rel;
  try {
    rel = decodeURIComponent(pathname);
  } catch {
    res.statusCode = 400;
    res.end("Bad request");
    return;
  }
  let file = path.normalize(path.join(dist, rel));
  // Block path traversal.
  if (file !== dist && !file.startsWith(dist + path.sep)) {
    res.statusCode = 403;
    res.end("Forbidden");
    return;
  }
  const isFile = fs.existsSync(file) && fs.statSync(file).isFile();
  const hasExt = path.extname(rel) !== "";
  if (!isFile) {
    if (hasExt) {
      res.statusCode = 404;
      res.end("Not found");
      return;
    }
    file = path.join(dist, "index.html"); // SPA fallback
  }
  const ext = path.extname(file);
  res.statusCode = 200;
  res.setHeader("Content-Type", MIME[ext] || "application/octet-stream");
  res.setHeader(
    "Cache-Control",
    file.includes(`${path.sep}assets${path.sep}`)
      ? "public, max-age=31536000, immutable"
      : "no-cache",
  );
  for (const [k, v] of Object.entries(SECURITY_HEADERS)) res.setHeader(k, v);
  fs.createReadStream(file).pipe(res);
}

http
  .createServer((req, res) => {
    proxy(req, res, () => serveStatic(req, res));
  })
  .listen(port, host, () => {
    console.log(`DocuMind dashboard: http://${host}:${port}`);
    if (!process.env.DOCUMIND_PROXY_API_KEY) {
      console.warn("WARNING: DOCUMIND_PROXY_API_KEY is not set; protected API calls will return 503.");
    }
  });
