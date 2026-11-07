import axios from "axios";

/**
 * Same-origin client. No credentials of any kind are attached in the browser:
 * the dashboard server/proxy adds the Bearer token server-side.
 */
export const http = axios.create({
  baseURL: "",
  timeout: 30_000,
  headers: { Accept: "application/json" },
});
