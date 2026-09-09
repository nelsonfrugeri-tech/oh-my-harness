import { preview } from "astro";

// The programmatic server stays attached to Playwright even inside an agent environment.
await preview({ server: { host: "127.0.0.1", port: 4321 } });
