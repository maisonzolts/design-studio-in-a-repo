# Svetlana cockpit

A deliberately small, loopback-only dashboard shell. It shows which integration adapters are configured without returning secret values or private records.

Original cockpit implementation credit: Tom Lyons.
License for cockpit code: MIT (`LICENSE`).

```bash
npm test
npm start
```

Add data panels behind `panels/index.js`. Keep secrets in environment variables and bind only to loopback. The private source cockpit included CRM, project, financial, health, and content panels; those data-coupled panels were intentionally excluded.
