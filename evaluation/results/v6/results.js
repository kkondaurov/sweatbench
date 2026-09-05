"use strict";

const mean = values => values.reduce((sum, value) => sum + value, 0) / values.length;
const median = values => {
  const ordered = [...values].sort((a, b) => a - b);
  const middle = Math.floor(ordered.length / 2);
  return ordered.length % 2 ? ordered[middle] : (ordered[middle - 1] + ordered[middle]) / 2;
};
const money = value => `$${value.toFixed(2)}`;
const integer = value => Math.round(value).toLocaleString("en-US");
const signed = value => value >= 0 ? `+${value}` : String(value);
const duration = seconds => {
  if (!Number.isFinite(seconds)) return "Not recorded";
  const minutes = Math.round(seconds / 60);
  const hours = Math.floor(minutes / 60);
  return hours ? `${hours}h ${String(minutes % 60).padStart(2, "0")}m` : `${minutes}m`;
};
const family = row => row.model === "GPT-6 Astra" ? "astra" : row.harness === "Codex CLI" ? "codex" : row.harness === "Claude Code" ? "claude" : "opencode";
const shortName = row => `${row.model.replace(/^GPT-(?:5\.6|6) /, "").replace(/^Meta /, "").replace(/^Claude /, "").replace(/ Pro 0813/, " Pro")} ${row.effort}`;
const estimateClass = row => row.costBasis === "estimated" ? "cost-estimate" : "";
const costBasisLabel = row => row.costBasis === "estimated" ? "API-equivalent" : "Recorded spend";

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
const state = { selected: "astra-low", score: "core", x: "cost", ranges: false, fullScale: false, search: "", harness: "all", sort: "default" };
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
    <div class="run-detail-header"><strong>${row.runs.length} completed ${row.runs.length === 1 ? "run" : "runs"}</strong><span>Sample total <span class="${estimateClass(row)}">${money(row.totalCost)}</span> (${costBasisLabel(row)}) · Average recovery ${signed(Number(row.avgRecovery.toFixed(1)))}</span></div>
    <div class="table-wrap"><table class="run-detail-table" aria-label="Runs for ${row.model} ${row.effort}, ${row.harness}">
      <thead><tr><th scope="col">Run</th><th scope="col">Core <span>out of 39</span></th><th scope="col">Maintenance <span>out of 10</span></th><th scope="col">Ship <span>out of 94</span></th><th scope="col">Final <span>out of 94</span></th><th scope="col">Recovery</th><th scope="col" title="Candidate-launched children; fixed harness workers excluded">Subagents</th><th scope="col">Production <span>lines of code</span></th><th scope="col">Tests <span>lines of code</span></th>${showRuntime ? '<th scope="col">Runtime</th>' : ""}<th scope="col">Cost <span>per run</span></th></tr></thead>
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
      <td data-label="Core" title="${row.avgCore.toFixed(1)} out of 39; observed range ${row.minCore}–${row.maxCore}">${scoreCell(row.avgCore, 39)}</td>
      <td data-label="Maintenance" title="${row.avgJudgment.toFixed(1)} out of 10">${scoreCell(row.avgJudgment, 10)}</td>
      <td data-label="Sweeps"><span class="summary-number">${row.sweeps} of ${row.runs.length}</span></td>
      <td data-label="Avg runtime"><span class="summary-number">${duration(row.avgRuntime)}</span></td>
      <td data-label="Cost per run" title="${costBasisLabel(row)} cost"><span class="summary-number ${estimateClass(row)}">${money(row.medianCost)}</span></td>
      <td data-label="Production lines" class="code-cell">${integer(row.medianProdLoc)}</td>
      <td data-label="Test lines" class="code-cell">${integer(row.medianTestLoc)}</td>
    </tr><tr id="details-${row.id}" class="run-detail-row"${expanded ? "" : " hidden"}><td colspan="8">${runDetails(row)}</td></tr>`;
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
    <dl class="selection-scores"><div><dt>Core · mean</dt><dd>${row.avgCore.toFixed(1)}<span>out of 39</span></dd></div><div><dt>Maintenance · mean</dt><dd>${row.avgJudgment.toFixed(1)}<span>out of 10</span></dd></div></dl>
    <dl class="selection-facts"><dt>Median cost</dt><dd class="${estimateClass(row)}">${money(row.medianCost)}</dd><dt>Average runtime</dt><dd>${duration(row.avgRuntime)}</dd><dt>Perfect sweeps</dt><dd>${row.sweeps} of ${row.runs.length}</dd></dl>
    <p class="selection-range">${costBasisLabel(row)} · range <span class="${estimateClass(row)}">${money(row.minCost)}–${money(row.maxCost)}</span></p>
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
  const margin = { left: 44, right: 36, top: 122, bottom: 52 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  const visible = filteredRows();
  const isCore = state.score === "core";
  const fullScale = Boolean(state.fullScale);
  const yMin = fullScale ? 0 : isCore ? 26 : 1;
  const maxScore = isCore ? 39 : 10;
  const rawKey = { cost: "cost", runtime: "runtimeSeconds", code: "prodLoc" }[state.x];
  const summaryKey = { cost: "medianCost", runtime: "avgRuntime", code: "medianProdLoc" }[state.x];
  const step = { cost: 10, runtime: 7200, code: 2000 }[state.x];
  const allValues = summaries.flatMap(row => row.runs.map(run => run[rawKey])).filter(Number.isFinite);
  const xMax = Math.ceil(Math.max(...allValues) / step) * step;
  const x = value => margin.left + value / xMax * innerWidth;
  const y = value => margin.top + (maxScore - value) / (maxScore - yMin) * innerHeight;
  const xFormat = value => state.x === "cost" ? `$${value}` : state.x === "runtime" ? `${value / 3600}h` : value ? `${value / 1000}k` : "0";
  const scoreKey = isCore ? "avgCore" : "avgJudgment";
  const scoreName = isCore ? "Core" : "Maintenance";
  const xTitle = { cost: "Median cost per run (USD)", runtime: "Average model runtime", code: "Median production LOC" }[state.x];
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  const scaleDescription = `${fullScale ? "Full" : "Focused"} score scale: ${yMin} to ${maxScore}${fullScale ? "" : "; baseline is not zero"}`;
  svg.setAttribute("aria-label", `Average ${scoreName} out of ${maxScore} versus ${xTitle}, ${visible.length} configurations. ${scaleDescription}.`);
  svg.setAttribute("data-score-min", yMin);
  svg.setAttribute("data-score-max", maxScore);
  svg.replaceChildren();
  const add = (tag, attrs, parent = svg, text = null) => {
    const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    if (text !== null) node.textContent = text;
    parent.appendChild(node);
    return node;
  };
  const yTicks = isCore ? fullScale ? [0, 10, 20, 30, 39] : [26, 30, 33, 36, 39] : fullScale ? [0, 2, 4, 6, 8, 10] : [1, 2, 4, 6, 8, 10];
  yTicks.forEach(tick => {
    add("line", { x1: margin.left, x2: width - margin.right, y1: y(tick), y2: y(tick), class: tick === maxScore ? "plot-max" : "plot-grid" });
    add("text", { x: margin.left - 9, y: y(tick) + 4, "text-anchor": "end", class: "plot-text" }, svg, tick);
  });
  for (let tick = 0; tick <= xMax; tick += step) {
    add("text", { x: x(tick), y: height - margin.bottom + 20, "text-anchor": "middle", class: "plot-text" }, svg, xFormat(tick));
  }
  add("line", { x1: margin.left, x2: width - margin.right, y1: height - margin.bottom, y2: height - margin.bottom, class: "plot-axis" });
  add("text", { x: margin.left, y: 16, class: "plot-axis-title" }, svg, `Average ${scoreName} (out of ${maxScore})`);
  add("text", { x: width - margin.right, y: 16, "text-anchor": "end", class: "plot-axis-title" }, svg, scaleDescription);
  add("text", { x: margin.left + innerWidth / 2, y: height - 3, "text-anchor": "middle", class: "plot-axis-title" }, svg, xTitle);

  const positions = visible.map(row => ({ row, cx: x(row[summaryKey]), cy: y(row[scoreKey]) }));
  // Tight clusters get smaller glyphs, never jittered coordinates.
  positions.forEach(p => {
    const nearest = Math.min(...positions.filter(other => other !== p).map(other => Math.hypot(other.cx - p.cx, other.cy - p.cy)));
    p.radius = Math.min(6, Math.max(.8, (nearest - 2) / 2));
  });
  positions.forEach(({ row, cx, cy }) => {
    if (!state.ranges && row.id !== state.selected) return;
    const color = `var(--${family(row)})`;
    const xs = row.runs.map(run => run[rawKey]);
    const ys = row.runs.map(run => run[state.score]);
    const rangeClass = `plot-range${row.id === state.selected ? " selected" : ""}`;
    add("line", { x1: x(Math.min(...xs)), x2: x(Math.max(...xs)), y1: cy, y2: cy, stroke: color, class: rangeClass });
    add("line", { x1: cx, x2: cx, y1: y(Math.min(...ys)), y2: y(Math.max(...ys)), stroke: color, class: rangeClass });
  });
  const leaders = add("g", { class: "plot-leaders", "aria-hidden": "true" });
  positions.forEach(position => {
    const { row, cx, cy } = position;
    const selected = row.id === state.selected;
    const group = add("g", { class: "plot-point", "data-model": row.id, tabindex: 0, role: "button", "aria-pressed": selected, style: `color:var(--${family(row)});--marker-stroke:${position.radius < 4 ? .6 : 2}px`, "aria-label": `${row.model} ${row.effort}: Core ${row.avgCore.toFixed(1)} out of 39, Maintenance ${row.avgJudgment.toFixed(1)} out of 10, median cost ${money(row.medianCost)}, ${row.runs.length} ${row.runs.length === 1 ? "run" : "runs"}` });
    position.group = group;
    add("title", {}, group, `${row.model} · ${row.effort}\nCore ${row.avgCore.toFixed(1)} out of 39 · Maintenance ${row.avgJudgment.toFixed(1)} out of 10\nMedian ${money(row.medianCost)} · ${row.runs.length} ${row.runs.length === 1 ? "run" : "runs"}`);
    if (selected) add("circle", { cx, cy, r: 10, class: "halo" }, group);
    const common = { fill: "currentColor", class: "mark" };
    const radius = position.radius, halfSide = radius / Math.SQRT2;
    if (family(row) === "opencode") add("rect", { x: cx - halfSide, y: cy - halfSide, width: halfSide * 2, height: halfSide * 2, ...common }, group);
    else if (family(row) === "claude") add("path", { d: `M${cx},${cy - radius}l${radius},${radius} -${radius},${radius} -${radius},-${radius}Z`, ...common }, group);
    else add("circle", { cx, cy, r: radius, ...common }, group);
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

  // Measure the actual SVG font, including padding, before choosing callouts.
  positions.forEach(position => {
    position.label = add("text", { x: 0, y: 0, class: "plot-label" }, position.group, shortName(position.row));
    const box = position.label.getBBox();
    position.labelWidth = Math.ceil(box.width) + 10;
    position.labelHeight = Math.ceil(box.height) + 8;
    position.baseline = 4 - box.y;
  });
  const overlaps = (a, b) => a.left < b.right + 3 && a.right + 3 > b.left && a.top < b.bottom + 3 && a.bottom + 3 > b.top;
  const crosses = (a, b) => {
    const turn = (x1, y1, x2, y2, x3, y3) => (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1);
    return turn(a.x1, a.y1, a.x2, a.y2, b.x1, b.y1) * turn(a.x1, a.y1, a.x2, a.y2, b.x2, b.y2) < -.01 &&
      turn(b.x1, b.y1, b.x2, b.y2, a.x1, a.y1) * turn(b.x1, b.y1, b.x2, b.y2, a.x2, a.y2) < -.01;
  };
  const throughBox = (line, box) => {
    // Slab intersection also catches collinear and endpoint contacts.
    let near = 0, far = 1;
    for (const [start, delta, min, max] of [[line.x1, line.x2 - line.x1, box.left - 2, box.right + 2], [line.y1, line.y2 - line.y1, box.top - 2, box.bottom + 2]]) {
      if (Math.abs(delta) < .001) { if (start < min || start > max) return false; }
      else {
        const a = (min - start) / delta, b = (max - start) / delta;
        near = Math.max(near, Math.min(a, b)); far = Math.min(far, Math.max(a, b));
        if (near > far) return false;
      }
    }
    return true;
  };
  const cacheKey = JSON.stringify([width, height, positions.map(p => [p.row.id, p.cx, p.cy, p.label.textContent, p.labelWidth, p.labelHeight])]);
  let layout = drawChart.labelLayout?.key === cacheKey ? drawChart.labelLayout.boxes : null;
  if (!layout) {
    const options = positions.map(p => {
      const candidates = [];
      const candidate = (left, top) => {
        const box = { left, top, right: left + p.labelWidth, bottom: top + p.labelHeight };
        if (left < margin.left + 4 || box.right > width - margin.right || top < 32 || box.bottom > height - margin.bottom - 12) return;
        if (positions.some(other => overlaps(box, { left: other.cx - 10, right: other.cx + 10, top: other.cy - 10, bottom: other.cy + 10 }))) return;
        const x2 = Math.max(left, Math.min(p.cx, box.right)), y2 = Math.max(top, Math.min(p.cy, box.bottom));
        const length = Math.hypot(x2 - p.cx, y2 - p.cy);
        const line = { x1: p.cx, y1: p.cy, x2, y2 };
        const blocked = positions.reduce((sum, other) => {
          if (other === p) return sum;
          const t = Math.max(0, Math.min(1, ((other.cx - p.cx) * (x2 - p.cx) + (other.cy - p.cy) * (y2 - p.cy)) / (length * length)));
          const distance = Math.hypot(other.cx - p.cx - t * (x2 - p.cx), other.cy - p.cy - t * (y2 - p.cy));
          return sum + (distance < other.radius + .8 ? 1 : 0);
        }, 0);
        candidates.push({ ...box, ...line, cost: length + blocked * 100000 });
      };
      for (let distance = 18; distance <= 270; distance += 18) {
        for (let direction = 0; direction < 16; direction++) {
          const angle = direction * Math.PI / 8;
          candidate(p.cx + Math.cos(angle) * (distance + p.labelWidth / 2) - p.labelWidth / 2,
            p.cy + Math.sin(angle) * (distance + p.labelHeight / 2) - p.labelHeight / 2);
        }
      }
      // A chart-wide fallback keeps every label visible even in dense clusters.
      for (let top = 32; top + p.labelHeight < height - margin.bottom - 12; top += p.labelHeight + 6) {
        for (let left = margin.left + 4; left + p.labelWidth <= width - margin.right; left += 28) candidate(left, top);
      }
      return candidates.sort((a, b) => a.cost - b.cost);
    });
    const cost = (box, placed, index) => {
      let total = box.cost;
      for (let j = 0; j < placed.length; j++) {
        if (j === index || !placed[j]) continue;
        if (overlaps(box, placed[j])) return Infinity;
        if (throughBox(box, placed[j]) || throughBox(placed[j], box)) total += 100000;
        if (crosses(box, placed[j])) total += 10000;
      }
      return total;
    };
    let bestCost = Infinity;
    for (let trial = 0; trial < 32; trial++) {
      const order = positions.map((_, index) => index).sort((a, b) => trial === 0 ? options[a].length - options[b].length :
        Math.sin((a + 1) * (trial + 1) * 127.1) - Math.sin((b + 1) * (trial + 1) * 127.1));
      const placed = Array(positions.length).fill(null);
      for (let pass = 0; pass < 6; pass++) {
        for (const index of order) {
          let best = null, score = Infinity;
          for (const box of options[index]) {
            if (box.cost >= score) break;
            const value = cost(box, placed, index);
            if (value < score) { best = box; score = value; }
          }
          placed[index] = best;
        }
      }
      const total = placed.some(box => !box) ? Infinity : placed.reduce((sum, box, index) => sum + cost(box, placed, index), 0);
      if (total < bestCost) { bestCost = total; layout = placed; }
      if (bestCost < 10000) break;
    }
    // Relocate conflicting pairs together; single-label moves can get trapped.
    for (let pass = 0; pass < 3; pass++) {
      for (let i = 0; i < layout.length; i++) for (let j = i + 1; j < layout.length; j++) {
        if (!crosses(layout[i], layout[j]) && !throughBox(layout[i], layout[j]) && !throughBox(layout[j], layout[i])) continue;
        const others = layout.map((box, index) => index === i || index === j ? null : box);
        const available = index => options[index].filter(box => cost(box, others, index) < 10000).slice(0, 100);
        const left = available(i), right = available(j);
        let pair = null, pairCost = Infinity;
        for (const a of left) for (const b of right) {
          if (a.cost + b.cost >= pairCost || overlaps(a, b) || crosses(a, b) || throughBox(a, b) || throughBox(b, a)) continue;
          pair = [a, b]; pairCost = a.cost + b.cost;
        }
        if (pair) { layout[i] = pair[0]; layout[j] = pair[1]; }
      }
    }
    drawChart.labelLayout = { key: cacheKey, boxes: layout };
  }
  positions.forEach((p, index) => {
    const box = layout[index];
    const connector = add("g", { class: `plot-connector${p.row.id === state.selected ? " active" : ""}`, "data-label-for": p.row.id, style: `color:var(--${family(p.row)})` }, leaders);
    add("line", { x1: p.cx, y1: p.cy, x2: box.x2, y2: box.y2, class: "plot-connector-back" }, connector);
    add("line", { x1: p.cx, y1: p.cy, x2: box.x2, y2: box.y2, class: "plot-connector-line" }, connector);
    const background = add("rect", { x: box.left, y: box.top, width: p.labelWidth, height: p.labelHeight, rx: 2, class: "plot-label-box" }, p.group);
    p.group.insertBefore(background, p.label);
    p.label.setAttribute("x", box.left + 5);
    p.label.setAttribute("y", box.top + p.baseline);
    p.group.addEventListener("mouseenter", () => connector.classList.add("active"));
    p.group.addEventListener("mouseleave", () => connector.classList.toggle("active", p.row.id === state.selected));
  });
  document.getElementById("plot-description").textContent = `${scaleDescription}. Average ${scoreName} score (out of ${maxScore}) against ${xTitle.charAt(0).toLowerCase() + xTitle.slice(1)}. ${state.ranges ? "Whiskers show observed run ranges, not confidence intervals." : "Range shown for the selected configuration."}${state.x === "cost" ? " Subscription costs are API-equivalent." : ""}`;
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
        <span class="condition-metric"><small>Core · mean</small><strong>${row.avgCore.toFixed(1)}</strong><span class="metric-limit">out of 39</span><span class="condition-track"><b style="width:${row.avgCore / 39 * 100}%"></b></span></span>
        <span class="condition-metric"><small>Maint. · mean</small><strong>${row.avgJudgment.toFixed(1)}</strong><span class="metric-limit">out of 10</span><span class="condition-track"><b style="width:${row.avgJudgment * 10}%"></b></span></span>
        <span class="condition-metric"><small>Sweeps</small><strong>${row.sweeps} of ${row.runs.length}</strong></span>
        <span class="condition-metric"><small>Cost · median</small><strong class="cost-estimate">${money(row.medianCost)}</strong></span>
        </summary><div class="run-detail-header" style="margin-top:20px">Median code: ${integer(row.medianProdLoc)} production / ${integer(row.medianTestLoc)} test LOC · Average final: ${mean(row.runs.map(run => run.final)).toFixed(1)} out of 94 scenarios</div>${runDetails(row, false)}</details>`;
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
document.getElementById("full-score-scale").addEventListener("change", event => { state.fullScale = event.target.checked; drawChart(); });
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
