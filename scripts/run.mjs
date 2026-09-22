import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { connect } from "node:net";
import next from "next";

const mode = process.argv[2] === "start" ? "start" : "dev";
const root = new URL("../", import.meta.url);
const hostname = process.env.MONITORAMENTO_HOST || "0.0.0.0";
const port = Number(process.env.PORT || 3000);
const livePort = Number(process.env.LIVE_WS_PORT || 3001);
const nextApp = next({
  dev: mode !== "start",
  hostname,
  port,
  dir: root.pathname,
});
await nextApp.prepare();
const handleRequest = nextApp.getRequestHandler();
const handleUpgrade = nextApp.getUpgradeHandler();

let worker = null;
let workerRestart = null;
let workerRestarts = 0;
let shuttingDown = false;

function startWorker() {
  worker = spawn(
    process.execPath,
    ["--experimental-strip-types", "scripts/worker.ts"],
    { cwd: root, stdio: "inherit" },
  );
  const startedAt = Date.now();
  worker.on("exit", (code, signal) => {
    if (shuttingDown) return;
    const lifetime = Date.now() - startedAt;
    workerRestarts = lifetime >= 60_000 ? 0 : workerRestarts + 1;
    const delay = Math.min(1_000 * 2 ** workerRestarts, 30_000);
    console.error(
      `Worker finalizado (${signal || `código ${code ?? "desconhecido"}`}); reiniciando em ${delay / 1_000}s.`,
    );
    workerRestart = setTimeout(startWorker, delay);
  });
}

const server = createServer((request, response) => {
  void handleRequest(request, response);
});

server.on("upgrade", (request, socket, head) => {
  const pathname = new URL(request.url || "/", "http://localhost").pathname;
  if (pathname !== "/api/live") {
    handleUpgrade(request, socket, head);
    return;
  }

  const upstream = connect(livePort, "127.0.0.1");
  upstream.once("connect", () => {
    const headers = Object.entries(request.headers).flatMap(([name, value]) => {
      if (Array.isArray(value)) return value.map((item) => `${name}: ${item}`);
      return value === undefined ? [] : [`${name}: ${value}`];
    });
    upstream.write(
      `${request.method} ${request.url} HTTP/${request.httpVersion}\r\n` +
        `${headers.join("\r\n")}\r\n\r\n`,
    );
    if (head.length) upstream.write(head);
    socket.pipe(upstream).pipe(socket);
  });
  upstream.on("error", () => socket.destroy());
  socket.on("error", () => upstream.destroy());
});

await new Promise((resolve, reject) => {
  server.once("error", reject);
  server.listen(port, hostname, resolve);
});
console.log(`▲ Next.js em http://localhost:${port}`);
console.log(`✓ WebSocket público em /api/live`);
startWorker();

// Recover the initial forecast after a deploy/restart. Normal refreshes remain
// driven by the Cloudflare cron, even when no browser is open.
if (process.env.OBJECT_STORAGE_URL && process.env.PUSH_INTERNAL_SECRET) {
  void (async () => {
    const base = `http://127.0.0.1:${port}`;
    const current = await fetch(`${base}/api/projection`, { signal: AbortSignal.timeout(15_000) });
    const payload = current.ok ? await current.json() : null;
    if (payload?.projection && Date.now() - Date.parse(payload.projection.generatedAt) < 15 * 60_000) return;
    const response = await fetch(`${base}/api/internal/projection-refresh`, {
      method: "POST",
      headers: { authorization: `Bearer ${process.env.PUSH_INTERNAL_SECRET}` },
      signal: AbortSignal.timeout(13 * 60_000),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    console.log("[projection] initial forecast ready");
  })().catch(error => console.error("[projection] initial calculation unavailable; cron will retry:", error.message));
}

async function shutdown(signal = "SIGTERM") {
  if (shuttingDown) return;
  shuttingDown = true;
  if (workerRestart) clearTimeout(workerRestart);
  worker?.kill(signal);
  await new Promise((resolve) => server.close(resolve));
  await nextApp.close();
}

process.once("SIGINT", () => void shutdown("SIGINT"));
process.once("SIGTERM", () => void shutdown("SIGTERM"));
