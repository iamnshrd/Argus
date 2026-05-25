const GITHUB_API_VERSION = "2022-11-28";

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(env) });
    }

    try {
      if (url.pathname === "/refresh" && request.method === "POST") {
        return json(await dispatchWorkflow(env), 202, env);
      }

      if (url.pathname === "/status" && request.method === "GET") {
        return json(await latestRun(env), 200, env);
      }

      return json({ error: "not_found" }, 404, env);
    } catch (error) {
      return json({ error: error.message || "request_failed" }, 500, env);
    }
  },
};

async function dispatchWorkflow(env) {
  await github(
    env,
    `/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/actions/workflows/${env.GITHUB_WORKFLOW_ID}/dispatches`,
    {
      method: "POST",
      body: JSON.stringify({ ref: env.GITHUB_REF || "main" }),
    },
  );

  return {
    ok: true,
    status: "queued",
    workflow: env.GITHUB_WORKFLOW_ID,
    ref: env.GITHUB_REF || "main",
  };
}

async function latestRun(env) {
  const params = new URLSearchParams({
    branch: env.GITHUB_REF || "main",
    event: "workflow_dispatch",
    per_page: "1",
  });
  const data = await github(
    env,
    `/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/actions/workflows/${env.GITHUB_WORKFLOW_ID}/runs?${params}`,
  );
  const run = data.workflow_runs?.[0];

  return {
    ok: true,
    run: run
      ? {
          id: run.id,
          status: run.status,
          conclusion: run.conclusion,
          createdAt: run.created_at,
          updatedAt: run.updated_at,
          url: run.html_url,
        }
      : null,
  };
}

async function github(env, path, init = {}) {
  if (!env.GITHUB_TOKEN) {
    throw new Error("GITHUB_TOKEN secret is not configured");
  }

  const response = await fetch(`https://api.github.com${path}`, {
    ...init,
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      "Content-Type": "application/json",
      "User-Agent": "Argus-Truth-Refresh-Worker",
      "X-GitHub-Api-Version": GITHUB_API_VERSION,
      ...(init.headers || {}),
    },
  });

  if (response.status === 204) return {};

  const text = await response.text();
  const data = text ? JSON.parse(text) : {};

  if (!response.ok) {
    throw new Error(data.message || `GitHub API failed: ${response.status}`);
  }

  return data;
}

function json(data, status, env) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      ...corsHeaders(env),
    },
  });
}

function corsHeaders(env) {
  return {
    "Access-Control-Allow-Origin": env.ALLOWED_ORIGIN || "https://iamnshrd.github.io",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Cache-Control": "no-store",
  };
}
