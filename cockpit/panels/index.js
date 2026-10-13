const definitions = [
  { id: "calendar", label: "Calendar", env: "GOOGLE_REFRESH_TOKEN", swap: "Google Workspace or another calendar API" },
  { id: "tasks", label: "Tasks", env: "MOTION_API_KEY", swap: "Motion or another task manager" },
  { id: "crm", label: "CRM", env: "HUBSPOT_ACCESS_TOKEN", swap: "HubSpot or another CRM" },
  { id: "records", label: "Records", env: "POCKETBASE_URL", swap: "PocketBase or another datastore" },
];

export function panelData(env = process.env) {
  return definitions.map((panel) => ({
    ...panel,
    state: env[panel.env] ? "configured" : "not configured",
  }));
}
