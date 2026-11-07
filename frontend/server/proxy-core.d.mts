import type { IncomingMessage, ServerResponse } from "node:http";

export function createApiProxy(options: {
  backendUrl: string;
  apiKey: string;
}): (req: IncomingMessage, res: ServerResponse, next?: () => void) => void;
