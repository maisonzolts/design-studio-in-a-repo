import assert from "node:assert/strict";
import test from "node:test";
import { panelData } from "../panels/index.js";

test("panels expose configuration state without secret values", () => {
  const panels = panelData({ HUBSPOT_ACCESS_TOKEN: "secret" });
  assert.equal(panels.find((p) => p.id === "crm").state, "configured");
  assert.equal(JSON.stringify(panels).includes("secret"), false);
});
