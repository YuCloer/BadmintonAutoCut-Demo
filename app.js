(function () {
  "use strict";

  const data = window.DEMO_METRICS;
  const selector = document.getElementById("arm-select");
  const byId = (id) => document.getElementById(id);
  const formatPct = (value) => `${Number(value).toFixed(2)}%`;
  const formatSeconds = (value) => Number(value).toFixed(2);

  function renderArm(armId) {
    const arm = data.arms.find((item) => item.id === armId) || data.arms[0];
    const total = data.scope.referenceIntervalCount;
    const ratio = (arm.completeMatches / total) * 100;

    byId("arm-name").textContent = arm.name;
    byId("matched").textContent = String(arm.completeMatches);
    byId("precision").textContent = formatPct(arm.pairPrecisionPct);
    byId("recall").textContent = formatPct(arm.pairRecallPct);
    byId("match-caption").textContent = `${arm.completeMatches} matched`;
    byId("match-bar").style.width = `${ratio.toFixed(2)}%`;
    byId("match-bar").setAttribute("aria-label", `${arm.completeMatches} of ${total} matched complete editorial intervals`);
    byId("live-lost").textContent = formatSeconds(arm.liveLostSeconds);
    byId("dead-kept").textContent = formatSeconds(arm.deadKeptSeconds);
    byId("unknown").textContent = formatPct(arm.unknownPct);
    byId("balanced-accuracy").textContent = formatPct(arm.balancedAccuracyPct);
    byId("live-recall").textContent = formatPct(arm.liveRecallPct);
    byId("dead-recall").textContent = formatPct(arm.deadRecallPct);
  }

  selector.addEventListener("change", (event) => renderArm(event.target.value));
  renderArm(selector.value);
}());
