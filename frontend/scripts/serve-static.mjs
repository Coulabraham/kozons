import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import path from "node:path";

const root = path.resolve("out");
const port = Number(process.env.PORT ?? 3000);
const host = process.env.HOST ?? "127.0.0.1";
const connectSources = process.env.KOZONS_CSP_CONNECT_SRC ?? "'self' http://localhost:8000 ws://localhost:8001";
const mimeTypes = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".webp": "image/webp",
};

async function resolveFile(urlPath) {
  const decoded = decodeURIComponent(urlPath.split("?", 1)[0]);
  const normalized = path.normalize(decoded).replace(/^[/\\]+/, "");
  if (normalized.startsWith("..")) return null;
  const requested = path.join(root, normalized || "index.html");
  const candidates = [requested, `${requested}.html`, path.join(requested, "index.html")];
  for (const candidate of candidates) {
    try {
      if ((await stat(candidate)).isFile()) return candidate;
    } catch {
      // Try the next static-export path shape.
    }
  }
  return path.join(root, "404.html");
}

createServer(async (request, response) => {
  try {
    const file = await resolveFile(request.url ?? "/");
    if (!file) {
      response.writeHead(400).end("Bad request");
      return;
    }
    const body = await readFile(file);
    response.writeHead(file.endsWith("404.html") ? 404 : 200, {
      "Content-Type": mimeTypes[path.extname(file)] ?? "application/octet-stream",
      "Cache-Control": file.includes(`${path.sep}_next${path.sep}`) ? "public, max-age=31536000, immutable" : "no-cache",
      "Content-Security-Policy": `default-src 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'; img-src 'self' data: blob: https:; media-src 'self' blob: https:; connect-src ${connectSources}; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'`,
      "Permissions-Policy": "camera=(), geolocation=(), microphone=(self)",
      "Referrer-Policy": "strict-origin-when-cross-origin",
      "X-Content-Type-Options": "nosniff",
      "X-Frame-Options": "DENY",
    });
    response.end(body);
  } catch {
    response.writeHead(500).end("Internal server error");
  }
}).listen(port, host, () => {
  console.log(`Kozons disponible sur http://${host}:${port}`);
});
