# Argus Truth Refresh Worker

Cloudflare Worker endpoint for manually triggering the Truth Social forecast Pages workflow.

## Endpoints

- `POST /refresh` triggers the `Truth Social Forecast Pages` GitHub Actions workflow.
- `GET /status` returns the latest manual workflow run.

## Deploy

```bash
npx wrangler login
npx wrangler secret put GITHUB_TOKEN --config workers/truth-refresh/wrangler.toml
npx wrangler deploy --config workers/truth-refresh/wrangler.toml
```

Use a fine-grained GitHub token scoped to this repository with Actions read/write access.

The current deployed endpoint is:

`https://argus-truth-refresh.iloveyaphets.workers.dev`
