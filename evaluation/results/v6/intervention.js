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
  document.getElementById("intervention-results-body").innerHTML = data.runs.map(run => {
    const baseline = summaries.find(row => row.id === run.baseline_group);
    const sourceLinks = baseline.runs.map((r, index) => `<a href="${sourceArchiveBaseUrl}/${r.id}" title="Baseline ${run.effort} run ${index + 1} source">${index + 1}</a>`).join(" · ");
    const effort = run.effort === "xhigh" ? "X-High" : run.effort[0].toUpperCase() + run.effort.slice(1);
    return `<tr class="intervention-baseline"><th scope="row"><strong>${effort}</strong><span>Earlier runs · 3</span><small>Source ${sourceLinks}</small></th>
      ${baselineCell(baseline.runs, "core", mean, score, "Core out of 39")}
      ${baselineCell(baseline.runs, "judgment", mean, score, "Maintenance out of 10")}
      ${cell(`${baseline.sweeps} of 3`, "Sweeps")}
      ${baselineCell(baseline.runs, "runtimeSeconds", mean, duration, "Runtime")}
      ${baselineCell(baseline.runs, "cost", median, money, "Cost per run")}
      ${baselineCell(baseline.runs, "prodLoc", median, integer, "Production lines")}
      ${baselineCell(baseline.runs, "testLoc", median, integer, "Test lines")}
    </tr><tr class="intervention-treatment"><th scope="row"><strong>${effort}</strong><span>With instruction · Run 1</span><small>${interventionSourceLink(run, "Source")}</small></th>
      ${cell(score(run.core), "Core out of 39")}${cell(score(run.maintenance), "Maintenance out of 10")}${cell("1 of 1", "Sweeps")}
      ${cell(duration(run.runtime_seconds), "Runtime")}${cell(money(run.cost), "Cost per run")}${cell(integer(run.prod_loc), "Production lines")}${cell(integer(run.test_loc), "Test lines")}
    </tr>`;
  }).join("");
  document.getElementById("intervention-structure-body").innerHTML = data.runs.map(run => {
    const effort = run.effort;
    const control = summaries.find(row => row.id === run.baseline_group);
    const productionChange = (run.prod_loc / control.medianProdLoc - 1) * 100;
    const costChange = (run.cost / control.medianCost - 1) * 100;
    return `<tr><th scope="row">${effort === "xhigh" ? "X-High" : effort[0].toUpperCase() + effort.slice(1)}</th><td>+${Math.round(productionChange)}%</td><td>+${Math.round(costChange)}%</td><td>${integer(run.structure.largest_production_file_loc)}</td></tr>`;
  }).join("");
  renderIcons(document.getElementById("intervention-view"));
}
