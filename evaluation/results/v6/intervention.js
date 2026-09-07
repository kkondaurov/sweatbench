"use strict";

const interventionArchiveUrl = readabilityIntervention.source_archive;
const interventionSourceLink = (run, label = "All seven snapshots") => `<a href="${interventionArchiveUrl}/${run.id}">${label} <i data-icon="ArrowUpRight"></i></a>`;

function renderIntervention() {
  const data = readabilityIntervention;
  document.getElementById("intervention-instruction-text").textContent = data.instruction;
  document.querySelectorAll("[data-intervention-archive]").forEach(link => { link.href = interventionArchiveUrl; });
  document.querySelectorAll("[data-intervention-code]").forEach(link => {
    link.href = `${interventionArchiveUrl.replace("/tree/", "/blob/")}/${link.dataset.interventionCode}`;
  });
  const score = value => value.toFixed(1);
  const cell = (value, label, range = "") => `<td data-label="${label}"><span class="summary-number">${value}</span>${range ? `<span class="intervention-range">${range}</span>` : ""}</td>`;
  const baselineCell = (runs, key, reduce, format, label) => {
    const values = runs.map(run => run[key]);
    const low = Math.min(...values), high = Math.max(...values);
    return cell(format(reduce(values)), label, low === high ? "" : `${format(low)}–${format(high)}`);
  };
  const groups = [...new Set(data.runs.map(run => run.baseline_group))].map(id => data.runs.filter(run => run.baseline_group === id));
  document.querySelector("#intervention-tab .tab-count").textContent = data.runs.length;
  document.getElementById("intervention-results-body").innerHTML = groups.map(runs => {
    const run = runs[0];
    const baseline = summaries.find(row => row.id === run.baseline_group);
    const sourceLinks = baseline.runs.map((r, index) => `<a href="${sourceArchiveBaseUrl}/${r.id}" title="Baseline ${run.model} ${run.effort} run ${index + 1} source">${index + 1}</a>`).join(" · ");
    const effort = run.effort === "xhigh" ? "X-High" : run.effort[0].toUpperCase() + run.effort.slice(1);
    const label = `${run.family === "astra" ? "Astra" : "Sol"} ${effort}`;
    const count = baseline.runs.length;
    const sweeps = runs.filter(r => r.core === 39 && r.maintenance === 10).length;
    return `<tr class="intervention-baseline"><th scope="row"><strong>${label}</strong><span>Earlier runs · ${count}</span><small>Source ${sourceLinks}</small></th>
      ${baselineCell(baseline.runs, "core", mean, score, "Core out of 39")}
      ${baselineCell(baseline.runs, "judgment", mean, score, "Maintenance out of 10")}
      ${cell(`${baseline.sweeps} of ${count}`, "Sweeps")}
      ${baselineCell(baseline.runs, "runtimeSeconds", mean, duration, "Runtime")}
      ${baselineCell(baseline.runs, "cost", median, money, "Cost per run")}
      ${baselineCell(baseline.runs, "prodLoc", median, integer, "Production lines")}
      ${baselineCell(baseline.runs, "testLoc", median, integer, "Test lines")}
    </tr><tr class="intervention-treatment"><th scope="row"><button class="intervention-run-toggle" data-intervention-group="${run.baseline_group}" aria-expanded="false"><i data-icon="ChevronRight"></i><span><strong>${label}</strong><span>With instruction · ${runs.length} runs</span></span></button></th>
      ${baselineCell(runs, "core", mean, score, "Core out of 39")}
      ${baselineCell(runs, "maintenance", mean, score, "Maintenance out of 10")}
      ${cell(`${sweeps} of ${runs.length}`, "Sweeps")}
      ${baselineCell(runs, "runtime_seconds", mean, duration, "Runtime")}
      ${baselineCell(runs, "cost", median, money, "Cost per run")}
      ${baselineCell(runs, "prod_loc", median, integer, "Production lines")}
      ${baselineCell(runs, "test_loc", median, integer, "Test lines")}
    </tr>${runs.map(r => `<tr class="intervention-run" data-intervention-detail="${run.baseline_group}" hidden><th scope="row"><strong>Run ${r.sample}</strong><small>${interventionSourceLink(r, "Source")}</small></th>
      ${cell(score(r.core), "Core out of 39")}${cell(score(r.maintenance), "Maintenance out of 10")}${cell(r.core === 39 && r.maintenance === 10 ? "Yes" : "No", "Sweep")}
      ${cell(duration(r.runtime_seconds), "Runtime")}${cell(money(r.cost), "Cost per run")}${cell(integer(r.prod_loc), "Production lines")}${cell(integer(r.test_loc), "Test lines")}
    </tr>`).join("")}`;
  }).join("");
  document.querySelectorAll(".intervention-run-toggle").forEach(button => {
    button.addEventListener("click", () => {
      const expanded = button.getAttribute("aria-expanded") !== "true";
      button.setAttribute("aria-expanded", String(expanded));
      document.querySelectorAll(`[data-intervention-detail="${button.dataset.interventionGroup}"]`).forEach(row => { row.hidden = !expanded; });
    });
  });
  document.getElementById("intervention-structure-body").innerHTML = groups.map(runs => {
    const run = runs[0];
    const effort = run.effort;
    const control = summaries.find(row => row.id === run.baseline_group);
    const productionChange = (median(runs.map(r => r.prod_loc)) / control.medianProdLoc - 1) * 100;
    const costChange = (median(runs.map(r => r.cost)) / control.medianCost - 1) * 100;
    const sizes = runs.map(r => r.structure.largest_production_file_loc);
    const signed = value => `${value >= 0 ? "+" : ""}${Math.round(value)}%`;
    return `<tr><th scope="row">${run.family === "astra" ? "Astra" : "Sol"} ${effort === "xhigh" ? "X-High" : effort[0].toUpperCase() + effort.slice(1)}</th><td>${signed(productionChange)}</td><td>${signed(costChange)}</td><td>${integer(median(sizes))}<span class="intervention-range">${integer(Math.min(...sizes))}–${integer(Math.max(...sizes))}</span></td></tr>`;
  }).join("");
  renderIcons(document.getElementById("intervention-view"));
}
