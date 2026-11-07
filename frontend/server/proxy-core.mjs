// Same-origin authenticating proxy used by BOTH the Vite dev/preview server and
// the production server (server/index.mjs).
//
// - Adds `Authorization: Bearer <key>` server-side. The key never reaches the browser.
// - Only forwards an explicit allow-list of routes (least privilege): the dashboard
//   cannot delete/update/create workflows even though the backend exposes those.
// - Any Authorization header sent by the browser is discarded.

const SEG = "[A-Za-z0-9._-]+";
const ID = "[0-9]{1,12}";

/** [method, pathRegex, requiresAuth] */
const ALLOWED = [
  ["GET", /^\/health$/, false],
  ["GET", /^\/api\/v1\/info$/, false],
  ["GET", /^\/api\/v1\/workflows\/?$/, true],
  ["GET", new RegExp(`^/api/v1/workflows/${ID}/details$`), true],
  ["GET", new RegExp(`^/api/v1/documents/${ID}$`), true],
  ["POST", new RegExp(`^/api/v1/documents/${ID}/approve$`), true],
  ["POST", new RegExp(`^/api/v1/documents/${ID}/reject$`), true],
  [
    "POST",
    new RegExp(`^/api/v1/github/repositories/${SEG}/${SEG}/pulls/${ID}/analyze$`),
    true,
  ],
];

const MAX_BODY_BYTES = 64 * 1024;
// PR analysis runs three agents and can take a while.
const UPSTREAM_TIMEOUT_MS = 5 * 60 * 1000;

function sendJson(res, status, body) {
  const payload = JSON.stringify(body);
  res.statusCode = status;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.setHeader("Cache-Control", "no-store");
  res.end(payload);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    req.on("data", (chunk) => {
      size += chunk.length;
      if (size > MAX_BODY_BYTES) {
        reject(Object.assign(new Error("Request body too large."), { status: 413 }));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

/**
 * @param {{ backendUrl: string, apiKey: string }} options
 * @returns {(req: import("node:http").IncomingMessage, res: import("node:http").ServerResponse, next?: () => void) => void}
 */
export function createApiProxy({ backendUrl, apiKey }) {
  const base = backendUrl.replace(/\/+$/, "");

  return async function apiProxy(req, res, next) {
    const url = new URL(req.url || "/", "http://localhost");
    const pathname = url.pathname;
    const method = (req.method || "GET").toUpperCase();

    // Non-secret diagnostics for the Settings page.
    if (pathname === "/__documind/proxy-status") {
      return sendJson(res, 200, {
        backend_url: base,
        api_key_configured: apiKey.length > 0,
      });
    }

    const isApiPath = pathname === "/health" || pathname.startsWith("/api/");
    if (!isApiPath) {
      if (next) return next();
      return sendJson(res, 404, { detail: "Not found." });
    }

    const rule = ALLOWED.find(([m, re]) => m === method && re.test(pathname));
    if (!rule) {
      return sendJson(res, 403, {
        detail: "This route is not exposed by the DocuMind dashboard proxy.",
      });
    }

    const requiresAuth = rule[2];
    if (requiresAuth && !apiKey) {
      return sendJson(res, 503, {
        detail:
          "The dashboard proxy has no API key configured. Set DOCUMIND_PROXY_API_KEY on the server.",
      });
    }

    try {
      const headers = { Accept: "application/json" };
      let body;

      if (method === "POST") {
        body = await readBody(req);
        if (body.length > 0) {
          headers["Content-Type"] = "application/json";
        }
      }
      if (requiresAuth) headers["Authorization"] = `Bearer ${apiKey}`;

      const upstream = await fetch(`${base}${pathname}${url.search}`, {
        method,
        headers,
        body: body && body.length > 0 ? body : undefined,
        redirect: "manual",
        signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
      });

      const buf = Buffer.from(await upstream.arrayBuffer());
      res.statusCode = upstream.status;
      res.setHeader(
        "Content-Type",
        upstream.headers.get("content-type") || "application/json",
      );
      res.setHeader("Cache-Control", "no-store");
      res.end(buf);
    } catch (err) {
      const status = err && typeof err === "object" && "status" in err ? Number(err.status) : 0;
      if (status === 413) return sendJson(res, 413, { detail: "Request body too large." });

      const timedOut = err instanceof Error && err.name === "TimeoutError";
      return sendJson(res, timedOut ? 504 : 502, {
        detail: timedOut
          ? "The backend took too long to respond."
          : "Unable to reach the DocuMind backend. Is it running?",
      });
    }
  };
}
