"use strict";

const mean = values => values.reduce((sum, value) => sum + value, 0) / values.length;
const median = values => {
  const ordered = [...values].sort((a, b) => a - b);
  const middle = Math.floor(ordered.length / 2);
  return ordered.length % 2 ? ordered[middle] : (ordered[middle - 1] + ordered[middle]) / 2;
};
const money = value => `$${value.toFixed(2)}`;
const integer = value => value.toLocaleString("en-US");
const signed = value => value >= 0 ? `+${value}` : String(value);
const duration = seconds => {
  if (!Number.isFinite(seconds)) return "Not recorded";
  const minutes = Math.round(seconds / 60);
  const hours = Math.floor(minutes / 60);
  return hours ? `${hours}h ${minutes % 60}m` : `${minutes}m`;
};
const family = row => row.model === "GPT-6 Astra" ? "astra" : row.harness === "Codex CLI" ? "codex" : row.harness === "Claude Code" ? "claude" : "opencode";
const shortName = row => `${row.model.replace(/^GPT-(?:5\.6|6) /, "").replace(/^Meta /, "").replace(/^Claude /, "").replace(/ Pro 0813/, " Pro")} ${row.effort}`;
const estimateClass = row => row.costBasis === "estimated" ? "cost-estimate" : "";

function summarize(row, index = 0) {
  const values = key => row.runs.map(run => run[key]).filter(Number.isFinite);
  return {
    ...row, index,
    avgCore: mean(values("core")), avgJudgment: mean(values("judgment")),
    avgRuntime: values("runtimeSeconds").length ? mean(values("runtimeSeconds")) : null,
    medianCost: median(values("cost")), totalCost: values("cost").reduce((a, b) => a + b, 0),
    medianProdLoc: median(values("prodLoc")), medianTestLoc: median(values("testLoc")),
    avgRecovery: mean(row.runs.map(run => run.final - run.ship)),
    sweeps: row.runs.filter(run => run.core === 39 && run.judgment === 10).length,
    minCore: Math.min(...values("core")), maxCore: Math.max(...values("core")),
    minCost: Math.min(...values("cost")), maxCost: Math.max(...values("cost"))
  };
}

const summaries = rows.map(summarize);
const expandedRows = new Set();
const state = { selected: "astra-low", score: "core", x: "cost", ranges: false, search: "", harness: "all", sort: "default" };
const sorters = {
  default: (a, b) => a.index - b.index,
  core: (a, b) => b.avgCore - a.avgCore || b.avgJudgment - a.avgJudgment,
  judgment: (a, b) => b.avgJudgment - a.avgJudgment || b.avgCore - a.avgCore,
  cost: (a, b) => a.medianCost - b.medianCost,
  runtime: (a, b) => a.avgRuntime - b.avgRuntime,
  code: (a, b) => a.medianProdLoc - b.medianProdLoc
};

function filteredRows() {
  return summaries.filter(row =>
    (state.harness === "all" || row.harness === state.harness) &&
    `${row.model} ${row.effort} ${row.harness} ${row.note || ""}`.toLowerCase().includes(state.search)
  ).sort(sorters[state.sort]);
}

function runDetails(row, showRuntime = true) {
  return `<div class="run-detail-panel">
    <div class="run-detail-header"><strong>${row.runs.length} completed ${row.runs.length === 1 ? "run" : "runs"}</strong><span>Sample total <span class="${estimateClass(row)}">${money(row.totalCost)}</span> · Average recovery ${signed(Number(row.avgRecovery.toFixed(1)))}</span></div>
    <div class="table-wrap"><table class="run-detail-table" aria-label="Runs for ${row.model} ${row.effort}, ${row.harness}">
      <thead><tr><th scope="col">Run</th><th scope="col">Core /39</th><th scope="col">Maintenance /10</th><th scope="col">Ship /94</th><th scope="col">Final /94</th><th scope="col">Recovery</th><th scope="col" title="Candidate-launched children; fixed harness workers excluded">Subagents</th><th scope="col">Prod LOC</th><th scope="col">Test LOC</th>${showRuntime ? '<th scope="col">Runtime</th>' : ""}<th scope="col">Cost</th></tr></thead>
      <tbody>${row.runs.map((run, index) => `<tr><td class="run-number">Run ${String(index + 1).padStart(2, "0")}</td><td>${run.core}</td><td>${run.judgment}</td><td>${run.ship}</td><td>${run.final}</td><td>${signed(run.final - run.ship)}</td><td>${run.subagents}</td><td>${integer(run.prodLoc)}</td><td>${integer(run.testLoc)}</td>${showRuntime ? `<td>${duration(run.runtimeSeconds)}</td>` : ""}<td class="run-cost ${estimateClass(row)}">${money(run.cost)}</td></tr>`).join("")}</tbody>
    </table></div>
  </div>`;
}

function scoreCell(value, max) {
  return `<span class="score-cell"><span class="summary-number">${value.toFixed(1)}</span><span class="score-track" aria-hidden="true"><span style="width:${value / max * 100}%"></span></span></span>`;
}

function renderTable() {
  const visible = filteredRows();
  document.getElementById("visible-count").textContent = visible.length;
  document.getElementById("empty-state").hidden = visible.length > 0;
  document.getElementById("results-body").innerHTML = visible.map(row => {
    const expanded = expandedRows.has(row.id);
    const extraNote = row.id.startsWith("ox-alpha") ? " · OX Alpha preview" : "";
    return `<tr class="summary-row${row.id === state.selected ? " selected" : ""}" data-row-id="${row.id}" style="--row-color:var(--${family(row)})" aria-expanded="${expanded}">
      <td><button id="toggle-${row.id}" class="model-toggle" aria-expanded="${expanded}" aria-controls="details-${row.id}" title="${expanded ? "Hide" : "Show"} runs for ${row.model} ${row.effort}"><i data-icon="ChevronRight"></i><span><span class="model-name">${row.model}<span class="effort">${row.effort}</span></span><span class="model-meta">${row.harness} · ${row.runs.length} ${row.runs.length === 1 ? "run" : "runs"}${extraNote}</span></span></button></td>
      <td data-label="Core /39" title="Observed range ${row.minCore}–${row.maxCore}">${scoreCell(row.avgCore, 39)}</td>
      <td data-label="Maintenance /10">${scoreCell(row.avgJudgment, 10)}</td>
      <td data-label="Sweeps"><span class="summary-number">${row.sweeps}<span class="muted">/${row.runs.length}</span></span></td>
      <td data-label="Avg runtime"><span class="summary-number">${duration(row.avgRuntime)}</span></td>
      <td data-label="Median cost"><span class="summary-number ${estimateClass(row)}">${money(row.medianCost)}</span></td>
      <td data-label="Prod / test LOC" class="code-cell">${integer(row.medianProdLoc)} <span>/ ${integer(row.medianTestLoc)}</span></td>
    </tr><tr id="details-${row.id}" class="run-detail-row"${expanded ? "" : " hidden"}><td colspan="7">${runDetails(row)}</td></tr>`;
  }).join("");
  renderIcons(document.getElementById("results-body"));
}

function toggleRow(id) {
  expandedRows.has(id) ? expandedRows.delete(id) : expandedRows.add(id);
  selectConfiguration(id, false);
  renderTable();
  document.getElementById(`toggle-${id}`).focus({ preventScroll: true });
}

function selectConfiguration(id, redraw = true) {
  state.selected = id;
  renderSelection();
  document.querySelectorAll(".summary-row").forEach(row => row.classList.toggle("selected", row.dataset.rowId === id));
  if (redraw) drawChart();
}

function renderSelection() {
  const row = summaries.find(item => item.id === state.selected);
  const panel = document.getElementById("selection-panel");
  if (!row) { panel.innerHTML = '<p class="section-note">No matching configurations.</p>'; return; }
  panel.innerHTML = `<div class="selection-heading"><div class="selection-kicker"><b class="legend-symbol ${family(row)}"></b>${row.harness}</div><h3 class="selection-title">${row.model}</h3><p class="selection-meta">${row.effort} reasoning · ${row.runs.length} completed ${row.runs.length === 1 ? "run" : "runs"}</p></div>
    <dl class="selection-scores"><div><dt>Core · mean</dt><dd>${row.avgCore.toFixed(1)}<span> /39</span></dd></div><div><dt>Maintenance · mean</dt><dd>${row.avgJudgment.toFixed(1)}<span> /10</span></dd></div></dl>
    <dl class="selection-facts"><dt>Median cost</dt><dd class="${estimateClass(row)}">${money(row.medianCost)}</dd><dt>Average runtime</dt><dd>${duration(row.avgRuntime)}</dd><dt>Perfect sweeps</dt><dd>${row.sweeps} of ${row.runs.length}</dd></dl>
    <p class="selection-range">Cost range <span class="${estimateClass(row)}">${money(row.minCost)}–${money(row.maxCost)}</span></p>
    <button class="text-button" id="selection-runs">View ${row.runs.length} ${row.runs.length === 1 ? "run" : "runs"}<i data-icon="ArrowDown"></i></button>`;
  renderIcons(panel);
  document.getElementById("selection-runs").addEventListener("click", () => {
    expandedRows.add(row.id);
    renderTable();
    const button = document.getElementById(`toggle-${row.id}`);
    button.scrollIntoView({ block: "start", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth" });
    button.focus({ preventScroll: true });
  });
}

function drawChart() {
  const svg = document.getElementById("cost-chart");
  if (document.getElementById("models-view").hidden) return;
  const width = Math.round(svg.clientWidth);
  const height = Math.round(svg.clientHeight);
  if (!width || !height) return;
  const compact = width < 550;
  const margin = { left: compact ? 32 : 38, right: compact ? 15 : 28, top: 27, bottom: 42 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  const visible = filteredRows();
  const isCore = state.score === "core";
  const yMin = isCore ? 26 : 1;
  const maxScore = isCore ? 39 : 10;
  const yMax = maxScore + (isCore ? .6 : .4);
  const rawKey = { cost: "cost", runtime: "runtimeSeconds", code: "prodLoc" }[state.x];
  const summaryKey = { cost: "medianCost", runtime: "avgRuntime", code: "medianProdLoc" }[state.x];
  const step = { cost: 10, runtime: 7200, code: 2000 }[state.x];
  const allValues = summaries.flatMap(row => row.runs.map(run => run[rawKey]));
  const xMax = Math.ceil(Math.max(...allValues) / step) * step;
  const x = value => margin.left + value / xMax * innerWidth;
  const y = value => margin.top + (yMax - value) / (yMax - yMin) * innerHeight;
  const xFormat = value => state.x === "cost" ? `$${value}` : state.x === "runtime" ? `${value / 3600}h` : value ? `${value / 1000}k` : "0";
  const scoreKey = isCore ? "avgCore" : "avgJudgment";
  const scoreName = isCore ? "Core" : "Maintenance";
  const xTitle = { cost: "Median cost per run (USD)", runtime: "Average model runtime", code: "Median production LOC" }[state.x];
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("aria-label", `Average ${scoreName} out of ${maxScore} versus ${xTitle}, ${visible.length} configurations`);
  svg.replaceChildren();
  const add = (tag, attrs, parent = svg, text = null) => {
    const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    if (text !== null) node.textContent = text;
    parent.appendChild(node);
    return node;
  };
  const yTicks = isCore ? [27, 30, 33, 36, 39] : [2, 4, 6, 8, 10];
  yTicks.forEach(tick => {
    add("line", { x1: margin.left, x2: width - margin.right, y1: y(tick), y2: y(tick), class: tick === maxScore ? "plot-max" : "plot-grid" });
    add("text", { x: margin.left - 9, y: y(tick) + 4, "text-anchor": "end", class: "plot-text" }, svg, tick);
  });
  for (let tick = 0; tick <= xMax; tick += compact && xMax / step > 4 ? step * 2 : step) {
    add("text", { x: x(tick), y: height - margin.bottom + 20, "text-anchor": "middle", class: "plot-text" }, svg, xFormat(tick));
  }
  add("line", { x1: margin.left, x2: width - margin.right, y1: height - margin.bottom, y2: height - margin.bottom, class: "plot-axis" });
  add("text", { x: margin.left, y: 12, class: "plot-axis-title" }, svg, `${scoreName} /${maxScore}`);
  add("text", { x: width - margin.right, y: 12, "text-anchor": "end", class: "plot-axis-title" }, svg, `${maxScore} = all checks passed`);
  add("text", { x: margin.left + innerWidth / 2, y: height - 3, "text-anchor": "middle", class: "plot-axis-title" }, svg, xTitle);

  const positions = visible.map(row => ({ row, cx: x(row[summaryKey]), cy: y(row[scoreKey]) }));
  positions.forEach(({ row, cx, cy }) => {
    if (!state.ranges && row.id !== state.selected) return;
    const color = `var(--${family(row)})`;
    const xs = row.runs.map(run => run[rawKey]);
    const ys = row.runs.map(run => run[state.score]);
    const rangeClass = `plot-range${row.id === state.selected ? " selected" : ""}`;
    add("line", { x1: x(Math.min(...xs)), x2: x(Math.max(...xs)), y1: cy, y2: cy, stroke: color, class: rangeClass });
    add("line", { x1: cx, x2: cx, y1: y(Math.min(...ys)), y2: y(Math.max(...ys)), stroke: color, class: rangeClass });
  });
  positions.forEach(({ row, cx, cy }) => {
    const selected = row.id === state.selected;
    const group = add("g", { class: "plot-point", "data-model": row.id, tabindex: 0, role: "button", "aria-pressed": selected, style: `color:var(--${family(row)})`, "aria-label": `${row.model} ${row.effort}: Core ${row.avgCore.toFixed(1)}/39, Maintenance ${row.avgJudgment.toFixed(1)}/10, median cost ${money(row.medianCost)}, ${row.runs.length} runs` });
    add("title", {}, group, `${row.model} · ${row.effort}\nCore ${row.avgCore.toFixed(1)} · Maintenance ${row.avgJudgment.toFixed(1)}\nMedian ${money(row.medianCost)} · ${row.runs.length} runs`);
    if (selected) add("circle", { cx, cy, r: 10, class: "halo" }, group);
    const common = { fill: "currentColor", class: "mark" };
    if (family(row) === "opencode") add("rect", { x: cx - 5, y: cy - 5, width: 10, height: 10, ...common }, group);
    else if (family(row) === "claude") add("path", { d: `M${cx},${cy - 7}l7,7 -7,7 -7,-7Z`, ...common }, group);
    else add("circle", { cx, cy, r: 6, ...common }, group);
    group.addEventListener("click", () => selectConfiguration(row.id));
    group.addEventListener("keydown", event => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault(); selectConfiguration(row.id);
        svg.querySelector(`[data-model="${row.id}"]`).focus();
      }
    });
    group.addEventListener("focus", () => {
      if (state.selected === row.id) return;
      selectConfiguration(row.id);
      svg.querySelector(`[data-model="${row.id}"]`).focus({ preventScroll: true });
    });
  });

  // Label only a few anchors at narrow widths; the selected point is always named.
  const priority = [state.selected, "astra-high", "sol-high", "luna-xhigh", "claude-opus5-high", "meta-muse-spark-1-3-high", "ox-alpha-high"];
  const candidates = [...positions].sort((a, b) => {
    const rank = id => priority.includes(id) ? priority.indexOf(id) : 100;
    return rank(a.row.id) - rank(b.row.id);
  }).filter(p => priority.includes(p.row.id)).slice(0, compact ? 3 : 7);
  const occupied = [];
  for (const { row, cx, cy } of candidates) {
    const label = add("text", { class: "plot-label" }, svg, shortName(row));
    const labelWidth = label.getComputedTextLength();
    const possible = [[12,-12],[12,20],[-labelWidth-12,-12],[-labelWidth-12,20],[12,36],[-labelWidth-12,36],[12,52],[-labelWidth-12,52], [12,72],[-labelWidth-12,72],[12,92],[-labelWidth-12,92]];
    let best = null;
    for (const [dx,dy] of possible) {
      const lx = Math.max(margin.left + 3, Math.min(cx + dx, width - margin.right - labelWidth));
      const ly = Math.max(margin.top + 14, Math.min(cy + dy, height - margin.bottom - 7));
      const box = { left: lx - 3, right: lx + labelWidth + 3, top: ly - 11, bottom: ly + 3 };
      const overlap = occupied.some(b => box.left < b.right && box.right > b.left && box.top < b.bottom && box.bottom > b.top);
      const pointOverlap = positions.some(p => p.cx + 7 > box.left && p.cx - 7 < box.right && p.cy + 7 > box.top && p.cy - 7 < box.bottom);
      if (!overlap && !pointOverlap) { best = { lx, ly, box }; break; }
    }
    if (!best) { label.remove(); continue; }
    label.setAttribute("x", best.lx); label.setAttribute("y", best.ly);
    if (Math.abs(best.ly - cy) > 26) {
      const line = add("line", { x1:cx, y1:cy+8, x2:Math.max(best.lx,Math.min(cx,best.lx+labelWidth)), y2:best.ly-12, stroke:`var(--${family(row)})`, "stroke-width":1, opacity:.5 });
      svg.insertBefore(line,label);
    }
    if (row.id === state.selected) label.setAttribute("font-weight", "650");
    occupied.push(best.box);
  }
  document.getElementById("plot-description").textContent = `Average ${scoreName} /${maxScore} against ${xTitle.charAt(0).toLowerCase() + xTitle.slice(1)}. ${state.ranges ? "Whiskers show observed run ranges, not confidence intervals." : "Range shown for the selected configuration."}${state.x === "cost" ? " ≈ API-equivalent estimate." : ""}`;
}

function renderHarnessComparison() {
  const comparisonOrder = ["sol-high", "sol-medium", "terra-xhigh", "luna-xhigh"];
  document.getElementById("harness-comparisons").innerHTML = comparisonOrder.map(id => {
    const model = rows.find(row => row.id === id);
    const conditions = [
      { key: "codex", name: "Codex CLI", runs: model.runs, color: "codex" },
      { key: "opencode", name: "OpenCode", runs: openCodeComparisonRuns[id], color: "opencode" },
      ...(id === "luna-xhigh" ? [{ key: "delegated", name: "Codex + delegation", runs: delegatedLunaComparisonRuns, color: "claude" }] : [])
    ];
    return `<section class="harness-group" aria-label="${model.model} ${model.effort}"><div class="harness-group-title"><h3>${model.model}</h3><p>${model.effort} reasoning</p></div><div>${conditions.map(condition => {
      const row = summarize({ ...model, harness: condition.name, runs: condition.runs, costBasis: "estimated" });
      return `<details class="harness-condition" id="harness-${id}-${condition.key}" style="--condition-color:var(--${condition.color})"><summary>
        <span class="condition-name"><i data-icon="ChevronRight"></i><span>${condition.name}<small>${row.runs.length} runs</small></span></span>
        <span class="condition-metric"><small>Core /39 · mean</small><strong>${row.avgCore.toFixed(1)}</strong><span class="condition-track"><b style="width:${row.avgCore / 39 * 100}%"></b></span></span>
        <span class="condition-metric"><small>Maint. /10 · mean</small><strong>${row.avgJudgment.toFixed(1)}</strong><span class="condition-track"><b style="width:${row.avgJudgment * 10}%"></b></span></span>
        <span class="condition-metric"><small>Sweeps</small><strong>${row.sweeps}/${row.runs.length}</strong></span>
        <span class="condition-metric"><small>Cost · median</small><strong class="cost-estimate">${money(row.medianCost)}</strong></span>
        </summary><div class="run-detail-header" style="margin-top:20px">Median code: ${integer(row.medianProdLoc)} production / ${integer(row.medianTestLoc)} test LOC · Average final: ${mean(row.runs.map(run => run.final)).toFixed(1)}/94</div>${runDetails(row, false)}</details>`;
    }).join("")}</div></section>`;
  }).join("");
  const audits = [
    ["Sol high", "sol-high", [95.0, 92.7], [6.8, 13.0]],
    ["Sol medium", "sol-medium", [94.6, 91.0], [5.8, 9.8]],
    ["Terra xhigh", "terra-xhigh", [95.9, 94.2], [2.6, 6.2]],
    ["Luna xhigh", "luna-xhigh", [96.0, 96.4, 96.7], [1.4, 7.6, 23.4]]
  ];
  document.getElementById("audit-body").innerHTML = audits.map(([name,id,cache,children]) => {
    const base = rows.find(row => row.id === id);
    const samples = [base.runs, openCodeComparisonRuns[id], ...(id === "luna-xhigh" ? [delegatedLunaComparisonRuns] : [])];
    const baseCost = median(base.runs.map(run => run.cost));
    return samples.map((runs,i) => {
      const cost = median(runs.map(run => run.cost));
      return `<tr class="${i === 0 ? "group-start" : ""}"><td>${i === 0 ? name : ""}</td><td>${["Codex CLI", "OpenCode", "Codex + delegation"][i]}</td><td>${cache[i].toFixed(1)}%</td><td>${children[i].toFixed(1)}</td><td class="cost-estimate">${money(cost)}</td><td>${i === 0 ? "Baseline" : `${signed(Math.round((cost / baseCost - 1) * 100))}%`}</td></tr>`;
    }).join("");
  }).join("");
  renderIcons(document.getElementById("harness-view"));
}

function refreshComparison() {
  const visible = filteredRows();
  if (!visible.some(row => row.id === state.selected)) state.selected = visible[0]?.id || null;
  renderTable(); renderSelection(); drawChart();
}

const methodAnchors = new Set(["overview", "scores", "sample", "costs", "code-time", "sources"]);
function activateView() {
  const hash = location.hash.slice(1);
  const view = methodAnchors.has(hash) || hash === "method" ? "method" : hash === "harness" ? "harness" : "models";
  document.querySelectorAll(".view-tab").forEach(tab => {
    const selected = tab.dataset.view === view;
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
    document.getElementById(`${tab.dataset.view}-view`).hidden = !selected;
  });
  if (view === "models") requestAnimationFrame(drawChart);
  if (methodAnchors.has(hash)) requestAnimationFrame(() => document.getElementById(hash).scrollIntoView({ block: "start" }));
  if (hash === "method") requestAnimationFrame(() => {
    const heading = document.getElementById("method-title");
    heading.scrollIntoView({ block: "start" });
    if (!document.activeElement.matches(".view-tab")) heading.focus({ preventScroll: true });
  });
}

document.getElementById("results-body").addEventListener("click", event => {
  const row = event.target.closest(".summary-row");
  if (row) { toggleRow(row.dataset.rowId); drawChart(); }
});
document.getElementById("model-search").addEventListener("input", event => { state.search = event.target.value.trim().toLowerCase(); refreshComparison(); });
document.getElementById("harness-filter").addEventListener("change", event => { state.harness = event.target.value; refreshComparison(); });
document.getElementById("sort-order").addEventListener("change", event => { state.sort = event.target.value; renderTable(); });
document.getElementById("chart-x").addEventListener("change", event => { state.x = event.target.value; drawChart(); });
document.getElementById("show-ranges").addEventListener("change", event => { state.ranges = event.target.checked; drawChart(); });
document.querySelectorAll("[data-score]").forEach(button => button.addEventListener("click", () => {
  state.score = button.dataset.score;
  document.querySelectorAll("[data-score]").forEach(other => other.setAttribute("aria-pressed", String(other === button)));
  drawChart();
}));
const tabs = [...document.querySelectorAll(".view-tab")];
tabs.forEach((tab, index) => {
  tab.addEventListener("click", () => { location.hash = tab.dataset.view; });
  tab.addEventListener("keydown", event => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    const next = event.key === "Home" ? 0 : event.key === "End" ? tabs.length - 1 : (index + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
    tabs[next].focus(); location.hash = tabs[next].dataset.view;
  });
});
window.addEventListener("hashchange", activateView);
let resizeFrame;
new ResizeObserver(() => { cancelAnimationFrame(resizeFrame); resizeFrame = requestAnimationFrame(drawChart); }).observe(document.querySelector(".chart-shell"));
document.getElementById("models-count").textContent = rows.reduce((count,row) => count + row.runs.length, 0);
document.getElementById("sample-summary").textContent = `${rows.length} configurations · ${rows.reduce((count,row) => count + row.runs.length, 0)} completed runs`;
renderIcons(); renderTable(); renderSelection(); renderHarnessComparison(); activateView();
