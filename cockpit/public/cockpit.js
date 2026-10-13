const panels = document.querySelector("#panels");

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function load() {
  const response = await fetch("/api/status", { cache: "no-store" });
  if (!response.ok) throw new Error(`status request failed (${response.status})`);
  const data = await response.json();

  document.querySelector("#name").textContent = data.name;
  document.querySelector("#subtitle").textContent = data.subtitle;
  panels.innerHTML = data.panels.map((panel) => `
    <article class="panel">
      <h3>${escapeHtml(panel.label)}</h3>
      <span class="state ${panel.state === "configured" ? "configured" : ""}">
        ${escapeHtml(panel.state)}
      </span>
      <p class="swap">${escapeHtml(panel.swap)}</p>
    </article>
  `).join("");
}

load().catch((error) => {
  panels.innerHTML = `<p class="error">${escapeHtml(error.message)}</p>`;
});
