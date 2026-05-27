const fmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });
const REFRESH_WORKER_URL = "https://argus-truth-refresh.iloveyaphets.workers.dev";

function cents(value) {
  return value === null || value === undefined ? "-" : `${fmt.format(value)}c`;
}

function integer(value) {
  return value === null || value === undefined ? "-" : `${Math.round(value)}`;
}

function edgeClass(value) {
  if (value === null || value === undefined) return "edge-flat";
  if (value >= 2) return "edge-positive";
  if (value <= -2) return "edge-negative";
  return "edge-flat";
}

function edge(value) {
  if (value === null || value === undefined) return "-";
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${fmt.format(value)}c`;
}

function setText(id, value) {
  document.getElementById(id).textContent = value;
}

function renderMarkets(markets) {
  const tbody = document.getElementById("marketRows");
  tbody.innerHTML = markets
    .map(
      (row) => `
        <tr>
          <td>${row.label}</td>
          <td>${cents(row.yesFair)}</td>
          <td>${cents(row.yesBid)} / ${cents(row.yesAsk)}</td>
          <td class="${edgeClass(row.yesEdgeAtAsk)}">${edge(row.yesEdgeAtAsk)}</td>
          <td>${cents(row.noFair)}</td>
          <td>${cents(row.noBid)} / ${cents(row.noAsk)}</td>
          <td class="${edgeClass(row.noEdgeAtAsk)}">${edge(row.noEdgeAtAsk)}</td>
        </tr>
      `,
    )
    .join("");
}

function renderTopics(topics) {
  const container = document.getElementById("topics");
  if (!topics.length) {
    container.textContent = "No posts yet.";
    return;
  }
  container.innerHTML = topics
    .map(
      (row) => `
        <div class="topic">
          <span>${row.topic}</span>
          <strong>${fmt.format(row.share * 100)}%</strong>
          <div class="bar"><span style="width: ${Math.max(2, row.share * 100)}%"></span></div>
        </div>
      `,
    )
    .join("");
}

function renderDailyProfile(rows) {
  document.getElementById("dailyRows").innerHTML = rows
    .map(
      (row) => `
        <tr>
          <td>${row.day}</td>
          <td>${fmt.format(row.mean)}</td>
          <td>${fmt.format(row.median)}</td>
          <td>${row.min}-${row.max}</td>
        </tr>
      `,
    )
    .join("");
}

function renderEvents(events) {
  const list = document.getElementById("events");
  if (!events.length) {
    list.innerHTML = "<li>No listed events in the lookahead window.</li>";
    return;
  }
  list.innerHTML = events.map((event) => `<li>${event.date}: ${event.name}</li>`).join("");
}

function renderForecast(data) {
  document.getElementById("marketLink").href = data.marketUrl;
  setText("observed", integer(data.observed));
  setText("p50", integer(data.forecast.mean ?? data.forecast.p50));
  setText("last24", integer(data.live.last24h));
  setText("last6", integer(data.live.last6h));
  setText("burst1", integer(data.live.largest1hBurst));
  setText("burst6", integer(data.live.largest6hBurst));
  setText("week", `Week: ${data.week.start} to ${data.week.end} ET`);

  const generated = new Date(data.generatedAt);
  setText("timestamp", `Updated ${generated.toLocaleString()}`);

  renderMarkets(data.markets);
  renderTopics(data.live.topics);
  renderDailyProfile(data.dailyProfile);
  renderEvents(data.live.futureEvents);
}

async function loadForecast() {
  const response = await fetch(`./data/forecast.json?v=${Date.now()}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  const data = await response.json();
  renderForecast(data);
  return data;
}

async function refreshModel() {
  const button = document.getElementById("refreshButton");
  button.disabled = true;
  button.textContent = "Refreshing...";
  const currentGeneratedAt = document.getElementById("timestamp").textContent;

  try {
    if (!REFRESH_WORKER_URL) {
      setText("timestamp", "Refreshing deployed data...");
      await loadForecast();
      return;
    }

    setText("timestamp", "Triggering model refresh...");
    const response = await fetch(`${REFRESH_WORKER_URL}/refresh`, { method: "POST" });
    if (!response.ok) throw new Error(`refresh endpoint failed: ${response.status}`);

    setText("timestamp", "Model refresh queued. Waiting for deploy...");
    await waitForUpdatedForecast(currentGeneratedAt);
  } finally {
    button.disabled = false;
    button.textContent = "Refresh model";
  }
}

async function waitForUpdatedForecast(previousTimestampText) {
  for (let attempt = 0; attempt < 12; attempt += 1) {
    await delay(10000);
    const data = await loadForecast();
    const generated = new Date(data.generatedAt).toLocaleString();
    if (`Updated ${generated}` !== previousTimestampText) return;
  }
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

document.getElementById("refreshButton").addEventListener("click", () => {
  refreshModel().catch((error) => {
    setText("timestamp", `Failed to refresh forecast data: ${error.message}`);
  });
});

loadForecast().catch((error) => {
  setText("timestamp", `Failed to load forecast data: ${error.message}`);
});
