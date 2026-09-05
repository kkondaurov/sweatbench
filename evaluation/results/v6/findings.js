"use strict";

const familyFindings = [
  {
    id: "astra", name: "GPT-6 Astra", nav: "Astra",
    groups: ["astra-low", "astra-medium", "astra-high", "astra-xhigh"],
    setup: "Codex CLI · Three runs each at low, medium, high and xhigh",
    paragraphs: [
      "<strong>The scored failures were at storage and restart boundaries.</strong> All twelve runs passed every ordinary private API test at every accepted milestone. Four failed the room upgrade: the old application stored an array of JSON-encoded strings, while the new migration expected an array of objects. Their own raw-SQL fixtures could reproduce that expectation without reproducing the old application's actual data.",
      "Six runs failed durable retry after a fresh server start. A decoder converted saved JSON keys to existing Elixir atoms, but the module defining some finance keys had not loaded yet. Reading a finance report first, or restarting only the database connection inside a warm VM, concealed the problem. Both later history checks stopped at replay; that is not evidence that all their downstream accounting rules were wrong.",
      "Across the twelve runs, these two patterns account for all 20 lost family points, with three runs affected by both. On disposable copies, decoding the nested room values repaired seven of the eight failing upgrade scenarios. Medium run 1 then exposed a second, previously blocked replay-key defect; a bounded key-mapping repair fixed the remaining case. The shared blocker was real, but it was not always the only bug.",
      "<strong>X-High swept all three runs.</strong> In runs 1 and 2, candidate-written fresh-server tests actually failed, prompted a replay fix and then passed. That is stronger evidence than simply having more tests. X-High cost 51% more than high at the median and took 80% longer on average, with 12% more production code. Low and high also produced a sweep; twelve runs do not establish a reliable effort ranking.",
      "A separate, unscored audit probe found a remaining distinction between two X-High sweeps. Both preserved a closed report and reached the same final balance, but only run 3 retained an offsetting credit revocation and expiry reversal. Run 1 omitted both categories despite reaching the same final balance. That paired HTTP check does not change the published scores; it shows a boundary the scored examples did not distinguish."
    ]
  },
  {
    id: "sol", name: "GPT-5.6 Sol", nav: "Sol",
    groups: ["sol-high", "sol-medium"],
    setup: "Codex CLI · Five high and five medium runs",
    paragraphs: [
      "<strong>Most runs held together through the full sequence.</strong> Six of ten swept: four high and two medium. The repeated weakness was a late use of credit that had already expired in a closed reporting period. The original closed report must stay fixed, while the later period reverses the relevant expiry. High run 4 and medium run 1 omitted that reversal, leaving the later liability wrong.",
      "Medium run 2 lost the same revival-related checks for a different reason. It had revival logic, but compared Elixir Date structs with ordinary comparison operators rather than calendar comparison. Valid report dates were rejected, and an opening balance omitted earlier issuance. A separate incomplete error-handling branch also crashed when asked to open an already-existing group. Medium run 4's credit-lifecycle failure was narrower still: an expiry field used 366 days instead of the required 365.",
      "The score therefore needs some unpacking. One late-credit assertion belongs to both a Core family and a Maintenance family; a second Maintenance case checks subsequent consumption of the revived credit. Those losses are related, not three independent discoveries. Sol was generally stronger than Luna on historical accounting, but a matching failure label does not prove a matching cause."
    ]
  },
  {
    id: "luna", name: "GPT-5.6 Luna", nav: "Luna",
    groups: ["luna-xhigh"],
    setup: "Codex CLI · Five xhigh runs",
    paragraphs: [
      "<strong>The recurring problem was preserving financial meaning as the product changed.</strong> All five runs failed the late-credit revival cluster. The broader failures varied: treating cumulative totals as daily activity, using a fixed opening balance, or reconstructing historical room funding from the current state. Four of the five runs had failures beyond revival and the narrow hotel-credit expiry field.",
      "Run 1 allocated room funding cash-first instead of preserving the recorded order of cash and credit. Its upgrade check reached the accounting assertions and returned the wrong answer, unlike Astra's early migration crashes. Run 3 used structural Date ordering for credit lots and could interpret exhausted funding as missing legacy data, rebuilding history that should have stayed exhausted.",
      "Run 2 is an important counterexample to reading the score as a list of conceptual mistakes. Its input accessor tried to convert a key to an existing atom before checking the string key. In a fresh server, valid requests could be read as missing. All eleven historical system checks failed while preparing ordinary business state, before the upgrade or restart under test. The same accessor also affected a destination revision guard. That gives a 12-family affected footprint, not proof that one patch would recover twelve points: other accounting defects remained.",
      "Luna's low inference cost did not translate into short runs: the median API-equivalent cost was $1.50, but average agent time was about two hours, with no sweeps. Separate harness and delegation experiments improved its results; they are not additional samples of this baseline and are kept in the Harnesses view."
    ]
  },
  {
    id: "terra", name: "GPT-5.6 Terra", nav: "Terra",
    groups: ["terra-xhigh"],
    setup: "Codex CLI · Five xhigh runs",
    paragraphs: [
      "<strong>The repeated misses concerned credit dates and closed-period accounting.</strong> Four runs returned credit-expiry dates one day later than required. Although the failing tests have names about credit ordering, their first failed comparisons show the expected remaining lot and amount with the wrong date. Those failures do not demonstrate incorrect ordering. Run 5 avoids the date error.",
      "All five fail late-credit restoration: an old-dated application arrives after the credit's expiry has appeared in a closed report. Keeping that report unchanged is only half the requirement; the next open report must record the restored liability. Four runs omit the restoration entry. Run 4 instead changes the open report's starting balance, so it does not preserve the required accounting trail either. The weakness appears in three related scoring families, not three independently established bugs.",
      "Runs 2 and 3 repaired some earlier payment and reporting failures in later milestones. Other upgrade checks still exposed incorrect historical balances or changed reports, so the recurring late-credit defect is not a complete explanation of every lost point. Final Core scores were tightly grouped at 36 to 37, with no sweeps and a median API-equivalent cost of $9.96."
    ]
  },
  {
    id: "gpt55", name: "GPT-5.5", nav: "GPT-5.5",
    groups: ["gpt-5-5-xhigh"],
    setup: "Codex CLI · Five xhigh runs",
    paragraphs: [
      "<strong>Four runs failed the room upgrade, for two quite different reasons.</strong> Runs 2 and 3 reversed a helper's returned values and passed the wrong kind of data into database-writing code. Their migrations crashed before the post-upgrade accounting could be tested. Runs 4 and 5 completed the upgrade but allocated historical cash before credit, losing the original mixed payment order. Those checks reached incorrect room balances, rather than stopping at startup.",
      "Four runs also missed the explicit entry restoring expired credit into the first open reporting day. Run 3 is the useful counterexample: it records the compensating credit movement and passes both restoration scenarios, despite separate migration and expiry-date failures. Run 1 passes every milestone check through milestone 6 before encountering the final restoration cases.",
      "No run swept. The median API-equivalent cost was $27.57, compared with Terra's $9.96, for a small difference in average scores. These cohorts used different CLI versions, and five samples are not enough to turn that comparison into a general ranking."
    ]
  },
  {
    id: "opus", name: "Claude Opus 5", nav: "Opus",
    groups: ["claude-opus5-high"],
    setup: "Claude Code · Two high runs",
    paragraphs: [
      "<strong>Both runs passed every historical upgrade and restart check, and both solved late-credit revival.</strong> Run 2 swept. Run 1's credit tests returned the expected surviving lot and amount, but its expiry date was one day later than required. This is a date-convention mismatch, not evidence of consuming credit in the wrong order.",
      "The other failure was a stale group total: after a transfer and cancellation, the cancelled destination still reported 500 cents of applied credit instead of zero. That stopped the test before its later shortfall-absorption and finance assertions. The implementation contained absorption logic; the failed family name is not enough to say that logic was absent or wrong.",
      "The sweep includes a candidate test explicitly checking that late redemption restores expired liability without rewriting closed history. It also has fewer final test declarations than the weaker run, 298 versus 356. API-equivalent costs were $43.96 and $51.35, with roughly two hours of agent work each. Two runs support these concrete contrasts, not a dependable sweep rate."
    ]
  },
  {
    id: "muse", name: "Meta Muse Spark 1.3", nav: "Muse Spark",
    groups: ["meta-muse-spark-1-3-high"],
    setup: "OpenCode · One high run",
    paragraphs: [
      "<strong>The single completed run left substantial integration work unfinished.</strong> It improved from 24 Core and 2 Maintenance points at delivery to 29 and 3 at final evaluation, recovering eleven scenarios. Milestone 7 supplied much of the previously missing finance reporting. Basic protocol, durable replay and several simpler upgrades worked, but historical accounting remained uneven.",
      "Several failures concerned disagreement between views of the same money. Partial cancellations and payment corrections reached a ledger that reported zero refunded cash when positive refunds were expected. Late receipts appeared in both ordinary movements and the separate late-adjustment section. A candidate test expected that duplication: a passing test was reinforcing the wrong contract.",
      "The two revival scenarios stopped before attempting revival. Closing a long reporting period exceeded the database connection's 15-second checkout limit. The code rebuilds every day's report inside the transaction and repeatedly scans earlier days. That supports a performance explanation, not a conclusion that revival arithmetic itself failed. One historical close check also stopped at the previous version's missing report endpoint, before the upgrade under test.",
      "The run cost $53.61 in recorded OpenRouter spend and took 9h 27m of agent time. It is the lowest-scoring model configuration in this sample, but one completed trajectory cannot tell us how typical that outcome is."
    ]
  },
  {
    id: "grok", name: "Grok 4.6", nav: "Grok",
    groups: ["grok-4-6-xhigh"],
    setup: "OpenCode · Five xhigh runs",
    paragraphs: [
      "<strong>Four runs passed every scored family outside the late-credit revival cluster.</strong> All five missed the situation where an old, still-valid credit application arrives after a report has already recorded its expiry. The closed report must stay unchanged while the first open period records restored liability.",
      "In four runs, the missing adjustment leaves the open period's closing liability at zero instead of 300 cents; the related consumption case also lacks the negative expiry entry. Run 1 instead changes the opening balance. These are different implementations of the same accounting-boundary failure. The basic scenario appears in two scoring families, with the consumption scenario providing a third family, so the three losses are not independent discoveries.",
      "Run 1 also has genuine funding-history errors: upgraded room allocations put cash in the wrong places, and a later cross-group payment reduction reports the wrong outstanding deposit. Those additional failures do not appear in the other four runs. Median recorded cost was $14.71 and average runtime 2h 03m. The sample shows broad implementation strength with a repeatable historical-accounting weakness."
    ]
  },
  {
    id: "qwen", name: "Qwen3.8 Max", nav: "Qwen",
    groups: ["qwen3-8-max-xhigh"],
    setup: "OpenCode · Five xhigh runs",
    paragraphs: [
      "<strong>The strongest and weakest runs tell quite different stories.</strong> Run 4 passes every Maintenance check, including late-credit revival, and misses only the hotel-credit family because its returned expiry date is one day late. Its code records the compensating expiry entry, and its own tests exercise an application arriving after a closed expiry.",
      "Run 5, the weakest, reverses only the ten-percent bonus when clawing back credit created from a cash cancellation, leaving the converted principal behind. Source review links that defect to failures across chargeback, payment-statement and shortfall checks. Its reports separately treat accumulated movements since reporting began as the current day's movements, while keeping opening balances fixed. Several reporting failures follow from that second mistake.",
      "Three runs fail old room-accounting upgrades after reaching numeric accounting assertions; these are not startup failures. Four miss a late-adjustment or revival-related case, but only three fail the basic revival case. Final Core ranges from 31 to 38 and Maintenance from 6 to 10. At a median recorded cost of $25.34 and average runtime of 4h 13m, the same configuration delivered substantial capability unevenly across these five samples."
    ]
  },
  {
    id: "deepseek", name: "DeepSeek V4 Pro 0813", nav: "DeepSeek",
    groups: ["deepseek-v4-pro-0813-max"],
    setup: "OpenCode · Five max runs",
    paragraphs: [
      "<strong>A date inconsistency spreads through several checks in runs 4 and 5.</strong> Credit stores the first unavailable day as its expiry date, while reporting waits until the day after that date to record expiry. The report is a day late. Two close-related scenarios stop at the initial missing expiry movement, before testing the later immutability or consumption assertions. Those outcomes do not independently demonstrate broken report freezing.",
      "All five separately fail the basic late-credit revival case, returning closing liability of zero instead of 300 cents. Four misallocate cash when upgrading old room history; run 1 passes both room-upgrade checks. Run 2 also keeps the reporting-inception credit balance as every day's opening balance and returns the wrong rejection when an already-charged payment arrives with a stale revision. Run 3's hotel-credit failure is different again: a missing zero-valued response field, not an expiry-date mismatch.",
      "Core ranges from 34 to 37 and Maintenance from 6 to 7, with no sweeps. Median recorded cost was $8.87, but average agent runtime was 4h 23m. The low cost did not imply fast completion, and the similar totals conceal distinct defects."
    ]
  },
  {
    id: "kimi", name: "Kimi K3", nav: "Kimi",
    groups: ["kimi-k3-max"],
    setup: "OpenCode · Five max runs",
    paragraphs: [
      "<strong>Late completion was a distinctive part of these trajectories.</strong> Four runs improved during later milestones, gaining nine scenarios on average across the five runs. In one, the transfer request exposed that the preceding room-accounting request had not actually been implemented. The agent added the missing allocations, payment corrections and statements along with transfers. That was useful recovery, but it did not make the earlier delivery complete; later feature work, not private-test feedback, exposed the missing foundation.",
      "All five failed accounting for credit applied after its expiry had already been closed. Some moved the revived amount into the opening balance; others omitted the negative expiry adjustment needed to restore liability in the open period. The strongest run finished at 38 Core and 8 Maintenance, with only the two revival scenarios failing. Its remaining gap was narrow, not a general inability to implement payments or transfers.",
      "The median recorded cost was $29.23. The combination of substantial recovery and a persistent reporting-boundary defect is more informative than either its cost or final score alone."
    ]
  },
  {
    id: "glm", name: "GLM 5.3", nav: "GLM 5.3",
    groups: ["glm-5-3-high"],
    setup: "OpenCode · Five high runs",
    paragraphs: [
      "<strong>One run solved the entire scored task; the other four did not share a single failure mechanism.</strong> The sweep preserved dated credit-lot events and explicitly recorded an expiry reversal when old credit was applied after a close. It is a concrete counterexample to treating the remaining failures as inevitable at this effort setting.",
      "The other four failed the revival scenarios at different points. Two stopped the longer scenario before revival was attempted because the initial expiry amount was wrong. Another completed the transferred-credit absorption steps correctly, then reported an opening liability of zero instead of 700 cents. That particular cross-feature failure was in reporting, not proof that absorption itself was broken.",
      "One trajectory changed a transfer function's return value without updating its caller, while leaving finance operations unwired. The next request repaired that foundation and recovered earlier behavior, but historical upgrade failures and some expiry errors remained. Final Core ranged from 33 to 39 and Maintenance from 6 to 10, at a median recorded cost of $20.96. The variation concerns both integration and historical accounting, not just one missed formula."
    ]
  },
  {
    id: "flash", name: "GLM-5.3 Flash", nav: "GLM-5.3 Flash",
    groups: ["ox-alpha-high", "ox-alpha-max"],
    setup: "OpenCode · Four high and four max runs · Includes OX Alpha preview samples",
    paragraphs: [
      "<strong>Seven runs returned credit-expiry dates one day too late.</strong> In a representative implementation, issuance stored an extra day and reporting then expired the lot on the following day. Four runs failed the longer revival scenario at its initial expiry assertion, before attempting revival. All eight failed the revival family overall, but that does not establish eight identical revival defects.",
      "In max run 3, a chargeback updated the payment's disposition while the ledger continued summing the original refund and conversion entries. The two views disagreed: refunded cash remained at 1,000 cents when the correction required zero. Other upgrade failures occurred at different stages, from room allocation to statement comparison; seven failed M4 upgrade checks did not mean seven migration crashes.",
      "There were useful successes: one high run passed the credit-lifecycle family, and all eight passed transfer mechanics and the durable-restart family. Median API-equivalent cost was $2.08 at high and $2.96 at max. High had slightly better average Core, max slightly better Maintenance; four runs per setting do not establish an effort effect."
    ]
  }
];

const historyNames = {
  "judgment-r1-policy-history": "Policy history",
  "judgment-r2-room-history": "Room history",
  "judgment-r3-payment-history": "Payment history",
  "judgment-r4-projection-history": "Finance projection history",
  "judgment-r5-close-history": "Period-close history",
  "judgment-c1-revival": "Expired-credit revival",
  "judgment-c2-late-cross-property-chargeback": "Late cross-property chargeback",
  "judgment-c3-transfer-shortfall-absorption": "Transfer and shortfall absorption",
  "judgment-c4-reporting-replay-purity": "Reporting replay purity",
  "judgment-c5-double-revival": "Revival followed by consumption"
};
const checkName = id => historyNames[id] || id.replaceAll("-", " ").replace(/^m(\d)/, "M$1").replace(/occ/g, "revision checks");
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
      <details class="finding-evidence"><summary>Run evidence</summary><p class="evidence-note">Final scores, retaining historical system checks. A listed check family may have stopped before reaching its later assertions. Core is out of 39; Maintenance is out of 10.</p>
      <div class="table-wrap"><table class="finding-run-table"><thead><tr><th>Run</th><th>Core</th><th>Maintenance</th><th>Failed check families</th></tr></thead><tbody>${runRows}</tbody></table></div></details>
    </section>`);
  }
}

renderFindings();
