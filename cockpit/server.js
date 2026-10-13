import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { config } from "./lib/config.js";
import { panelData } from "./panels/index.js";

const root = fileURLToPath(new URL("./public", import.meta.url));
const types = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8" };

export const server = createServer(async (req, res) => {
  if (req.url === "/api/status") {
    res.setHeader("content-type", "application/json");
    res.end(JSON.stringify({ name: config.name, subtitle: config.subtitle, panels: panelData() }));
    return;
  }
  const pathname = req.url === "/" ? "/index.html" : String(req.url || "").split("?")[0];
  if (pathname.includes("..")) {
    res.writeHead(400).end("bad path");
    return;
  }
  try {
    const body = await readFile(join(root, pathname));
    res.setHeader("content-type", types[extname(pathname)] || "application/octet-stream");
    res.end(body);
  } catch {
    res.writeHead(404).end("not found");
  }
});

if (process.env.NODE_ENV !== "test") {
  server.listen(config.port, config.host, () => {
    console.log(`Svetlana cockpit: http://${config.host}:${config.port}`);
  });
}
