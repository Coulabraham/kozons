import { spawn } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";

const edgePath = process.env.EDGE_PATH ?? "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const appUrl = process.env.KOZONS_PREVIEW_URL ?? "http://127.0.0.1:3000/";
const outputDirectory = path.resolve(".qa");
const debugPort = 9333;
const profiles = path.join(os.tmpdir(), `kozons-edge-cdp-${Date.now()}`);
const viewports = [
  { width: 375, height: 812 },
  { width: 768, height: 1024 },
  { width: 1440, height: 900 },
];

await mkdir(outputDirectory, { recursive: true });
const edge = spawn(edgePath, [
  "--headless=new",
  "--disable-gpu",
  "--hide-scrollbars",
  "--no-first-run",
  `--remote-debugging-port=${debugPort}`,
  `--user-data-dir=${profiles}`,
  "about:blank",
], { stdio: "ignore", windowsHide: true });

const pause = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));
async function waitForDebugger() {
  for (let attempt = 0; attempt < 50; attempt += 1) {
    try {
      const response = await fetch(`http://127.0.0.1:${debugPort}/json/list`);
      if (response.ok) {
        const pages = await response.json();
        const page = pages.find((entry) => entry.type === "page");
        if (page?.webSocketDebuggerUrl) return page.webSocketDebuggerUrl;
      }
    } catch {
      // Edge is still starting.
    }
    await pause(100);
  }
  throw new Error("Edge DevTools n'a pas démarré.");
}

let sequence = 0;
const pending = new Map();
let socket;
function command(method, params = {}) {
  const id = ++sequence;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
  });
}

try {
  const debuggerUrl = await waitForDebugger();
  socket = new WebSocket(debuggerUrl);
  await new Promise((resolve, reject) => {
    socket.addEventListener("open", resolve, { once: true });
    socket.addEventListener("error", reject, { once: true });
  });
  socket.addEventListener("message", (event) => {
    const payload = JSON.parse(event.data);
    if (!payload.id || !pending.has(payload.id)) return;
    const request = pending.get(payload.id);
    pending.delete(payload.id);
    if (payload.error) request.reject(new Error(payload.error.message));
    else request.resolve(payload.result);
  });
  await command("Page.enable");
  await command("Runtime.enable");

  const results = [];
  for (const viewport of viewports) {
    await command("Emulation.setDeviceMetricsOverride", {
      width: viewport.width,
      height: viewport.height,
      deviceScaleFactor: 1,
      mobile: viewport.width < 1024,
      screenWidth: viewport.width,
      screenHeight: viewport.height,
    });
    await command("Page.navigate", { url: `${appUrl}?qa=${viewport.width}` });
    for (let attempt = 0; attempt < 30; attempt += 1) {
      await pause(500);
      const readiness = await command("Runtime.evaluate", {
        expression: `({
          ready: document.body.innerText.includes('Se connecter') &&
            document.body.innerText.includes('Créer un compte') &&
            Boolean(document.querySelector('img[alt="Logo Kozons"]')?.complete) &&
            (document.querySelector('img[alt="Logo Kozons"]')?.naturalWidth ?? 0) > 0,
          error: Array.from(document.querySelectorAll('nextjs-portal')).some((portal) =>
            /Console Error|Runtime Error|Unhandled Runtime Error/.test(portal.shadowRoot?.innerText ?? '')
          )
        })`,
        returnByValue: true,
      });
      if (readiness.result.value.error || readiness.result.value.ready) break;
    }
    const evaluation = await command("Runtime.evaluate", {
      expression: `(() => ({
        innerWidth: window.innerWidth,
        innerHeight: window.innerHeight,
        scrollWidth: document.documentElement.scrollWidth,
        scrollHeight: document.documentElement.scrollHeight,
        horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth,
        stillLoading: document.body.innerText.includes('Ouverture de Kozons'),
        hasRuntimeError: Array.from(document.querySelectorAll('nextjs-portal')).some((portal) =>
          /Console Error|Runtime Error|Unhandled Runtime Error/.test(portal.shadowRoot?.innerText ?? '')
        ),
        pathname: window.location.pathname,
        hasLoginForm: Boolean(document.querySelector('input[name="identifier"]') && document.querySelector('input[name="password"]')),
        hasRegisterLink: document.querySelector('a[href="/auth/register"]')?.textContent?.includes('Créer un compte') ?? false,
        hasLogo: Boolean(document.querySelector('img[alt="Logo Kozons"]')?.complete) &&
          (document.querySelector('img[alt="Logo Kozons"]')?.naturalWidth ?? 0) > 0,
        hasDemoData: /Amina|Brice|Chloé|Équipe Kozons/.test(document.body.innerText),
        title: document.title,
        visibleText: document.body.innerText.slice(0, 160)
      }))()`,
      returnByValue: true,
    });
    const screenshot = await command("Page.captureScreenshot", {
      format: "png",
      captureBeyondViewport: false,
      fromSurface: true,
    });
    await writeFile(path.join(outputDirectory, `login-${viewport.width}.png`), Buffer.from(screenshot.data, "base64"));
    const metrics = evaluation.result.value;
    results.push({ requested: viewport, ...metrics });
    if (
      metrics.innerWidth !== viewport.width || metrics.horizontalOverflow || metrics.hasRuntimeError || metrics.stillLoading ||
      metrics.pathname !== "/auth/login" || !metrics.hasLoginForm || !metrics.hasRegisterLink || !metrics.hasLogo || metrics.hasDemoData
    ) {
      throw new Error(`Viewport ${viewport.width}px invalide: ${JSON.stringify(metrics)}`);
    }
  }
  console.log(JSON.stringify(results, null, 2));
} finally {
  if (socket?.readyState === WebSocket.OPEN) socket.close();
  edge.kill();
}
