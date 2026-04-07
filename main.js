const metrics = [
  {
    id: "bytes_recv",
    key: "bytes_recv",
    label: "Bytes Received",
    kind: "bytes",
  },
  {
    id: "bytes_sent",
    key: "bytes_sent",
    label: "Bytes Sent",
    kind: "bytes",
  },
  { id: "cpu", key: "cpu_percent", label: "CPU", kind: "percent" },
  {
    id: "memory",
    key: "memory_percent",
    label: "Memory",
    kind: "percent",
  },
  {
    id: "connections",
    key: "active_connections",
    label: "Connections",
    kind: "count",
  },
  { id: "latency", key: "latency_ms", label: "Latency", kind: "ms" },
];

const margin = { top: 20, right: 20, bottom: 30, left: 75 };
const svgSel = (id) => d3.select(`#${id}-chart svg`);

const width = +svgSel("bytes_recv").attr("width") - margin.left - margin.right;
const height =
  +svgSel("bytes_recv").attr("height") - margin.top - margin.bottom;

const x = d3.scaleTime().range([0, width]);

const formatters = {
  bytes: d3.format(".3~s"),
  percent: (v) => `${v.toFixed(1)}%`,
  count: d3.format(","),
  ms: (v) => (v == null ? "—" : `${v.toFixed(1)} ms`),
};

const yTickFormat = {
  bytes: d3.format(".2~s"),
  percent: (v) => `${v}%`,
  count: d3.format(","),
  ms: (v) => `${v} ms`,
};

const charts = {};
metrics.forEach((m) => {
  const svg = svgSel(m.id);
  const g = svg
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  const y = d3.scaleLinear().range([height, 0]);

  const line = d3
    .line()
    .defined((d) => d.value != null && !Number.isNaN(d.value))
    .x((d) => x(d.timestamp))
    .y((d) => y(d.value));

  g.append("g")
    .attr("class", `axis axis--x ${m.id}`)
    .attr("transform", `translate(0,${height})`);

  g.append("g").attr("class", `axis axis--y ${m.id}`);

  g.append("path").attr("class", `line ${m.id}`);

  charts[m.id] = { g, y, line, meta: m };
});

function parseSeries(raw, key) {
  return raw.map((d) => ({
    timestamp: new Date(d.timestamp * 1000),
    value: d[key] === null || d[key] === undefined ? null : +d[key],
  }));
}

function setValueText(metricId, kind, series) {
  const el = document.getElementById(`${metricId}-value`);
  if (!el) return;

  const last = series[series.length - 1];
  if (!last) {
    el.textContent = "—";
    return;
  }

  const v = last.value;
  if (v == null || Number.isNaN(v)) {
    el.textContent = "—";
    return;
  }

  if (kind === "bytes") {
    el.textContent = `${formatters.bytes(v)}B/s`;
  } else if (kind === "percent") {
    el.textContent = formatters.percent(v);
  } else if (kind === "count") {
    el.textContent = formatters.count(v);
  } else if (kind === "ms") {
    el.textContent = formatters.ms(v);
  } else {
    el.textContent = String(v);
  }
}

async function update() {
  try {
    const data = await d3.json("network_data.json");
    if (!Array.isArray(data) || data.length === 0) return;

    const timestamps = data.map((d) => new Date(d.timestamp * 1000));
    x.domain(d3.extent(timestamps));

    metrics.forEach((m) => {
      const chart = charts[m.id];
      const series = parseSeries(data, m.key);

      const maxVal =
        d3.max(series, (d) =>
          d.value == null || Number.isNaN(d.value) ? undefined : d.value,
        ) ?? 0;

      const paddedMax = maxVal === 0 ? 1 : maxVal * 1.15;

      if (m.kind === "percent") {
        chart.y.domain([0, 100]);
      } else {
        chart.y.domain([0, paddedMax]).nice();
      }

      chart.g.select(`.line.${m.id}`).datum(series).attr("d", chart.line);

      chart.g.select(`.axis--x.${m.id}`).call(d3.axisBottom(x).ticks(5));
      chart.g.select(`.axis--y.${m.id}`).call(
        d3
          .axisLeft(chart.y)
          .ticks(5)
          .tickFormat(yTickFormat[m.kind] || d3.format("~s")),
      );

      setValueText(m.id, m.kind, series);
    });
  } catch (err) {
    console.error("Error fetching or parsing data:", err);
  }
}

update();
setInterval(update, 1000);
