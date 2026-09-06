"use strict";

const familyFindings = [
  {
    id: "astra", name: "GPT-6 Astra", nav: "Astra",
    groups: ["astra-low", "astra-medium", "astra-high", "astra-xhigh"],
    setup: "Codex CLI · Three runs each at low, medium, high and xhigh",
    paragraphs: [
      "<strong>Astra's failures appeared when upgrading an old database or restarting the server.</strong> All twelve runs passed the regular API tests at every milestone. Four then failed to upgrade the previous version's room data: the migration expected room objects, but the old application had stored them as JSON text that needed another decoding step. Several of the agent's own tests inserted example data directly into the database in the format the new code expected, so they missed the mismatch.",
      "Six runs broke when an already-completed request was sent again after a server restart. The application should return the saved response without doing the work twice. Instead, the code reading that response depended on field names loaded into memory by another module. After a restart, that module had not loaded, and the request failed. Opening a finance report first happened to load it and make the problem disappear. Tests that restarted only the database connection also missed the bug because the server itself kept running.",
      "These two problems explain all 20 lost points across the twelve runs; three runs had both. To check how much else was broken, we repaired copies of the four failing migrations and reran their upgrade tests. Fixing the JSON decoding was enough for seven of the eight tests to pass. The eighth, in medium run 1, then reached the saved-response bug described above. Fixing that made it pass too. The published scores still reflect the original code.",
      "<strong>All three xhigh runs earned full marks.</strong> In runs 1 and 2, the agent wrote tests that started a new server, saw the repeated request fail, and fixed it before delivery. Those tests caught a problem that the weaker runs left behind. Compared with high, xhigh cost 51% more at the median, took 80% longer on average and produced 12% more production code. Low and high each also had a full-score run.",
      "A follow-up test, outside the scored benchmark, found a difference between xhigh runs 1 and 3. After a payment was reversed, the report needed two correcting entries: one withdrawing credit and one undoing its earlier expiry. The amounts cancelled each other out. Run 3 recorded both; run 1 omitted both. Both left the closed report unchanged and reached the correct final balance. The extra test shows how a balance can be right while the record of what happened is incomplete."
    ]
  },
  {
    id: "sol", name: "GPT-5.6 Sol", nav: "Sol",
    groups: ["sol-high", "sol-medium"],
    setup: "Codex CLI · Five high and five medium runs",
    paragraphs: [
      "<strong>Six of ten runs earned full marks: four high and two medium.</strong> Two of the remaining runs missed the same reporting correction. The test involves hotel credit used before it expires, but recorded in the application after a finance report has already marked the credit as expired. The reporting period is closed, so that report must stay unchanged and the correction belongs in the next open report. High run 4 and medium run 1 left out this correction, which made the next report show the wrong amount of credit owed.",
      "Medium run 2 tried to make that correction, but its date comparisons went wrong. It used Elixir's ordinary comparison operators on Date values instead of comparing calendar dates. The application rejected valid report dates and left earlier credit issuance out of an opening balance. It also crashed when asked to open a group that already existed. Medium run 4 had a smaller mistake: it returned an expiry date 366 days after issuance instead of the required 365.",
      "The late-credit mistake has a larger effect on the score than its single cause might suggest. The basic test counts toward both Core and Maintenance, and another Maintenance test uses the restored credit afterwards. Missing the correction can therefore cost three points across two tests."
    ]
  },
  {
    id: "luna", name: "GPT-5.6 Luna", nav: "Luna",
    groups: ["luna-xhigh"],
    setup: "Codex CLI · Five xhigh runs",
    paragraphs: [
      "<strong>Luna repeatedly lost track of how a balance had been reached.</strong> Some daily reports showed all transactions since reporting began as if they had happened that day, or reused the same opening balance every day. All five runs failed the tests for late-recorded credit use. Four also had failures beyond that case and the credit-expiry date.",
      "The room upgrades show the problem clearly. Run 1 assigned old payments to rooms by putting cash before credit, even when the payments had arrived in a different order. The resulting room balances were wrong. Run 3 sorted credit by Elixir's internal Date representation rather than calendar order. It could also mistake funding that had been fully used up for missing data and reconstruct it as though it were still available.",
      "Run 2 had an additional bug in the code that read incoming requests. After a fresh server start, it could treat supplied fields as missing. All eleven upgrade and restart tests stopped while creating the initial bookings and payments, before they could test the version change. The same bug also affected a check that rejects transfers based on an outdated destination record. A single request-reading error thus caused failures across much of the suite, alongside the run's separate accounting mistakes.",
      "The median API-equivalent cost was $1.50, with about two hours of agent work per run and no full-score runs. Luna did better in separate experiments with a different coding tool or delegation instructions; those results are in the Harnesses tab."
    ]
  },
  {
    id: "terra", name: "GPT-5.6 Terra", nav: "Terra",
    groups: ["terra-xhigh"],
    setup: "Codex CLI · Five xhigh runs",
    paragraphs: [
      "<strong>Credit dates and corrections to later reports were the repeated problems.</strong> Four of the five runs returned an expiry date one day later than required. At that point in the tests, they had the right remaining credit and amount; the date was wrong. Run 5 avoided this error.",
      "All five mishandled credit use recorded after a report had already marked the credit as expired. Four omitted the correction from the next open report. Run 4 changed that report's starting balance instead of recording a separate correction. The same mistake affected three scoring groups, through the basic late-credit test and a second test that used the restored credit.",
      "Runs 2 and 3 fixed some earlier payment and reporting bugs while implementing later features. Other upgrade tests still found wrong balances or reports that no longer matched the previous version. Final Core scores ranged from 36 to 37, with no full-score runs and a median API-equivalent cost of $9.96."
    ]
  },
  {
    id: "gpt55", name: "GPT-5.5", nav: "GPT-5.5",
    groups: ["gpt-5-5-xhigh"],
    setup: "Codex CLI · Five xhigh runs",
    paragraphs: [
      "<strong>Four runs failed the room upgrade.</strong> Runs 2 and 3 mixed up two values returned by a helper function, then sent the wrong data to the database. The migration crashed. Runs 4 and 5 completed the migration, but assigned old payments to rooms cash-first, losing the original order of cash and credit. Their upgraded applications ran, but reported wrong room balances.",
      "Four runs also missed the report correction for credit use recorded after expiry had been reported and closed. Run 3 handled this correctly and passed both related tests, despite its separate migration and expiry-date bugs. Run 1 passed every milestone check through milestone 6, then failed these final reporting cases.",
      "None earned full marks. The median API-equivalent cost was $27.57, compared with Terra's $9.96, for a small difference in average scores. The two cohorts also used different versions of Codex CLI."
    ]
  },
  {
    id: "opus", name: "Claude Opus 5", nav: "Opus",
    groups: ["claude-opus5-high"],
    setup: "Claude Code · Two high runs",
    paragraphs: [
      "<strong>Both runs passed every upgrade and restart test, and run 2 earned full marks.</strong> Both also handled credit used before expiry but recorded only after a closed report had marked it expired. Run 1 lost a Core point because it returned an expiry date one day late, even though the remaining credit and amount were correct.",
      "Run 1's other failure was a total that had not been updated. After a transfer and cancellation, the cancelled destination still showed 500 cents of applied credit instead of zero. The test stopped there, before checking credit availability, ledger balances and the finance report.",
      "Run 2's own tests included the difficult late-credit case: correcting the current report while leaving the closed one unchanged. It finished with fewer test declarations than run 1, 298 versus 356, while passing every scored check. The two runs cost $43.96 and $51.35 at API-equivalent prices and took roughly two hours each."
    ]
  },
  {
    id: "muse", name: "Meta Muse Spark 1.3", nav: "Muse Spark",
    groups: ["meta-muse-spark-1-3-high"],
    setup: "OpenCode · One high run",
    paragraphs: [
      "<strong>Muse Spark was still filling in earlier features at the last milestone.</strong> Milestone 7 added much of the finance reporting that milestone 6 had requested. Later work brought eleven previously failing scenarios to a pass, raising Core from 24 to 29 and Maintenance from 2 to 3. Basic request handling, returning saved responses after a restart and several simpler upgrades worked.",
      "The accounting records often disagreed with one another. After partial cancellations and payment corrections, the ledger showed no refunded cash where refunds should have appeared. Reports put late receipts in both the ordinary transaction totals and the separate late-adjustment section. The agent had written a test that expected this duplication, so its own passing test confirmed the mistake.",
      "Long reporting periods exposed another problem. Closing a period rebuilt every daily report and repeatedly scanned earlier days, all within one database transaction. This ran past the 15-second connection limit. Both tests of late-recorded credit use timed out during the close, before they could try the credit operation. Another upgrade test could not even create its starting report because the earlier version was missing the report endpoint.",
      "This single run cost $53.61 in recorded OpenRouter charges and took 9h 27m. It left Muse Spark with the lowest average score among the model configurations tested here."
    ]
  },
  {
    id: "grok", name: "Grok 4.6", nav: "Grok",
    groups: ["grok-4-6-xhigh"],
    setup: "OpenCode · Five xhigh runs",
    paragraphs: [
      "<strong>Four of five runs passed everything except the late-recorded credit cases.</strong> All five failed to correct the current report when a valid use of credit was recorded after its expiry report had closed. Four left the closing amount of credit owed at zero instead of 300 cents. Run 1 changed the opening balance instead of adding the required correction.",
      "This one omission cost three points: the basic case appears in both Core and Maintenance, and a second Maintenance case uses the restored credit. It accounts for all the lost points in runs 2 through 5.",
      "Run 1 also assigned old cash payments to the wrong rooms during an upgrade. Later, a payment reduction involving two groups produced the wrong outstanding deposit. Across the five runs, median recorded cost was $14.71 and average runtime was 2h 03m."
    ]
  },
  {
    id: "qwen", name: "Qwen3.8 Max", nav: "Qwen",
    groups: ["qwen3-8-max-xhigh"],
    setup: "OpenCode · Five xhigh runs",
    paragraphs: [
      "<strong>Qwen ranged from nearly complete to several connected accounting failures.</strong> Run 4 passed every Maintenance check and missed only a credit-expiry date, which it returned one day late. It made the required report correction for late-recorded credit use, and its own tests covered that case.",
      "Run 5 had a more fundamental mistake. When withdrawing credit created from a cash cancellation, it removed only the ten-percent bonus and left the original converted amount available. That error affected chargebacks, payment statements and checks of how unpaid amounts were covered. Separately, its daily reports treated all transactions since reporting began as today's transactions and reused a fixed opening balance.",
      "Three runs completed the old-room upgrade but returned wrong accounting values afterwards. The final scores ranged from 31 to 38 Core and 6 to 10 Maintenance. Median recorded cost was $25.34 and average runtime was 4h 13m."
    ]
  },
  {
    id: "deepseek", name: "DeepSeek V4 Pro 0813", nav: "DeepSeek",
    groups: ["deepseek-v4-pro-0813-max"],
    setup: "OpenCode · Five max runs",
    paragraphs: [
      "<strong>Runs 4 and 5 disagreed with themselves about when credit expired.</strong> They stored the first day credit could no longer be used as its expiry date, but the reports waited until the following day to show the expiry. Two longer tests stopped at this missing entry, before they could check what happened after closing the report or using credit later.",
      "All five runs also missed the report correction for late-recorded credit use, showing zero credit owed instead of 300 cents. Four assigned cash to the wrong rooms when upgrading old payment history; run 1 passed both room-upgrade tests.",
      "Other mistakes differed by run. Run 2 reused the credit balance from the start of reporting as every day's opening balance. Run 3 omitted a response field whose value should have been zero. Core scores ranged from 34 to 37 and Maintenance from 6 to 7. Median recorded cost was $8.87, with 4h 23m of agent work on average."
    ]
  },
  {
    id: "kimi", name: "Kimi K3", nav: "Kimi",
    groups: ["kimi-k3-max"],
    setup: "OpenCode · Five max runs",
    paragraphs: [
      "<strong>Kimi often finished earlier work while implementing the next feature.</strong> In one run, the request for transfers exposed that the preceding room-accounting feature was still missing. The agent added room allocations, payment corrections and statements along with transfers. It discovered the gap through the new request; it could not see the evaluator's results. Four runs improved during later milestones, gaining nine passing scenarios on average across all five runs.",
      "All five still mishandled late-recorded credit use. Some changed the current report's opening balance; others left out the correction needed to undo the earlier reported expiry. The strongest run finished at 38 Core and 8 Maintenance, with only these two reporting tests failing.",
      "Median recorded cost was $29.23. Much of the later work successfully repaired earlier omissions, while the late-credit reporting problem remained in every run."
    ]
  },
  {
    id: "glm", name: "GLM 5.3", nav: "GLM 5.3",
    groups: ["glm-5-3-high"],
    setup: "OpenCode · Five high runs",
    paragraphs: [
      "<strong>One run earned full marks, keeping a dated history of changes to each credit amount.</strong> When a late-recorded use of credit contradicted an expiry already shown in a closed report, it added a correction to the current report. The other four failed the related tests, though some went wrong earlier in the sequence: two reported an incorrect initial expiry amount, so the longer test stopped before attempting the late credit use.",
      "Another test showed a smaller gap between correct operations and incorrect reporting. The application correctly used transferred credit to cover an unpaid amount, then reported zero credit owed at the start of the reporting day instead of 700 cents.",
      "One run also broke transfers by changing a function's return value without updating the code that called it, and left finance operations disconnected from the request handler. Work on the next milestone repaired those omissions. Some expiry errors and previously recorded upgrade failures remained. Final Core scores ranged from 33 to 39 and Maintenance from 6 to 10, at a median recorded cost of $20.96."
    ]
  },
  {
    id: "flash", name: "GLM-5.3 Flash", nav: "GLM-5.3 Flash",
    groups: ["ox-alpha-high", "ox-alpha-max"],
    setup: "OpenCode · Four high and four max runs · Includes OX Alpha preview samples",
    paragraphs: [
      "<strong>Seven of eight runs returned an expiry date one day late.</strong> In one inspected implementation, the date was stored a day too late and the report waited yet another day to record the expiry. Four runs stopped the longer late-credit test at its first expiry check. All eight failed the group of tests covering report corrections for late-recorded credit use.",
      "Max run 3 also left the ledger out of sync with a corrected payment. A chargeback updated the payment record, but the ledger continued adding up the original refund and conversion entries. It still reported 1,000 cents of refunded cash where the corrected amount should have been zero. Room upgrades produced a mixture of failures: some applications returned wrong allocations or statements, while one migration crashed.",
      "All eight runs passed the transfer-mechanics tests and correctly returned saved responses after a server restart. One high run also passed the credit-lifecycle tests. Median API-equivalent cost was $2.08 at high and $2.96 at max. High had slightly better average Core scores; max had slightly better Maintenance scores."
    ]
  }
];

const checkNames = {
  "batch-protocol-validation": "Request validation and batch processing",
  "chargeback-reclassification": "Updating payment records after a chargeback",
  "cross-group-correction-provenance": "Following payment corrections across groups",
  "durable-idempotency": "Repeated requests and saved responses",
  "entitlement-clawback-shortfall": "Withdrawing credit and covering resulting shortfalls",
  "finance-close-immutability": "Keeping closed reports unchanged",
  "finance-effective-dating": "Recording transactions on the correct reporting day",
  "finance-report-correctness": "Cash and credit report totals",
  "finance-report-determinism": "Consistent reports without changing the underlying records",
  "hotel-credit-lifecycle": "Issuing, using, expiring and restoring credit",
  "late-adjustment-posting": "Recording corrections after a reporting period closes",
  "m2-migration": "Policy upgrade (milestone 2)",
  "m3-restart": "Saved responses after a server restart (milestone 3)",
  "m4-migration": "Room-accounting upgrade (milestone 4)",
  "m5-migration": "Transfer upgrade (milestone 5)",
  "m6-finance-upgrade": "Finance-reporting upgrade (milestone 6)",
  "m7-close-upgrade": "Period-close upgrade (milestone 7)",
  "multi-group-occ": "Rejecting transfers based on outdated group records",
  "partial-cancellation-settlement": "Refunds and credit after cancelling selected rooms",
  "payment-reduction": "Reducing a recorded payment",
  "payment-statement": "Payment statements",
  "room-funding-allocation": "Assigning cash and credit to rooms",
  "transfer-mechanics": "Transfers between groups",
  "judgment-r1-policy-history": "Preserving past bookings and settlements through a policy upgrade",
  "judgment-r2-room-history": "Reconstructing room funding from old payment history",
  "judgment-r3-payment-history": "Preserving old payments through transfers and corrections",
  "judgment-r4-projection-history": "Starting reports from existing financial history",
  "judgment-r5-close-history": "Closing reports created by an earlier version",
  "judgment-c1-revival": "Report corrections for late-recorded credit use",
  "judgment-c2-late-cross-property-chargeback": "Late cross-property chargeback",
  "judgment-c3-transfer-shortfall-absorption": "Using returned transferred credit to cover its original shortfall",
  "judgment-c4-reporting-replay-purity": "Keeping repeated requests out of report totals",
  "judgment-c5-double-revival": "Using credit after correcting its previously reported expiry"
};
const checkName = id => checkNames[id] || id.replaceAll("-", " ").replace(/^m(\d)/, "M$1").replace(/occ/g, "revision checks");
const escapeFinding = value => String(value).replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);

function renderFindings() {
  const nav = document.getElementById("findings-nav");
  const content = document.getElementById("family-findings");
  for (const item of familyFindings) {
    const runs = findingsEvidence.runs.filter(run => item.groups.includes(run.group)).sort((a, b) => item.groups.indexOf(a.group) - item.groups.indexOf(b.group) || a.sample - b.sample);
    const sweeps = runs.filter(run => run.core_final === 39 && run.maintenance_final === 10).length;
    nav.insertAdjacentHTML("beforeend", `<a href="#findings-${item.id}">${item.nav}</a>`);
    const runRows = runs.map(run => {
      const failures = run.final_failed_families;
      return `<tr><th scope="row" title="${escapeFinding(run.id)}">${escapeFinding(run.effort)} ${String(run.sample).padStart(2, "0")}</th><td>${run.core_final}</td><td>${run.maintenance_final}</td><td>${failures.length ? `<ul>${failures.map(id => `<li title="${escapeFinding(id)}">${escapeFinding(checkName(id))}</li>`).join("")}</ul>` : "None"}</td></tr>`;
    }).join("");
    content.insertAdjacentHTML("beforeend", `<section id="findings-${item.id}" class="family-finding">
      <h3>${item.name}</h3><p class="finding-meta">${runs.length} completed ${runs.length === 1 ? "run" : "runs"} · ${sweeps} ${sweeps === 1 ? "sweep" : "sweeps"}<br>${item.setup}</p>
      ${item.paragraphs.map(paragraph => `<p>${paragraph}</p>`).join("")}
      <details class="finding-evidence"><summary>Run results</summary><p class="evidence-note">Core is out of 39; Maintenance is out of 10. These are the final scores, including upgrade and restart results recorded at earlier milestones. Several failed check groups can share the same cause.</p>
      <div class="table-wrap"><table class="finding-run-table"><thead><tr><th>Run</th><th>Core</th><th>Maintenance</th><th>Failed check groups</th></tr></thead><tbody>${runRows}</tbody></table></div></details>
    </section>`);
  }
}

renderFindings();
