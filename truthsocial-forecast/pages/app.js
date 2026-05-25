const fmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });

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
          <td>${integer(row.noAskQuantity)}</td>
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

async function main() {
  const response = await fetch(`./data/forecast.json?v=${Date.now()}`, { cache: "no-store" });
  const data = await response.json();

  document.getElementById("marketLink").href = data.marketUrl;
  setText("observed", integer(data.observed));
  setText("p10", integer(data.forecast.p10));
  setText("p50", integer(data.forecast.p50));
  setText("p90", integer(data.forecast.p90));
  setText("last24", integer(data.live.last24h));
  setText("last6", integer(data.live.last6h));
  setText("burst1", integer(data.live.largest1hBurst));
  setText("burst6", integer(data.live.largest6hBurst));
  setText("week", `${data.week.start} to ${data.week.end} ET`);

  const generated = new Date(data.generatedAt);
  const now = new Date(data.nowEt);
  setText(
    "timestamp",
    `Generated ${generated.toLocaleString()} · model time ${now.toLocaleString()}`,
  );

  renderMarkets(data.markets);
  renderTopics(data.live.topics);
  renderDailyProfile(data.dailyProfile);
  renderEvents(data.live.futureEvents);
}

main().catch((error) => {
  setText("timestamp", `Failed to load forecast data: ${error.message}`);
});
