import { resolve } from "node:path";

export const config = Object.freeze({
  host: "127.0.0.1",
  port: Number(process.env.COCKPIT_PORT || 4321),
  name: process.env.COCKPIT_NAME || "SVETLANA",
  subtitle: process.env.COCKPIT_SUBTITLE || "LOCAL OPERATIONS",
  workdir: resolve(process.env.COCKPIT_WORKDIR || process.cwd()),
});
