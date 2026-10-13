(function () {
  "use strict";

  const language = document.documentElement.lang === "zh-CN" ? "zh-CN" : "en";
  const words = {
    en: {
      loading: "Loading the archived comparison…",
      loadFailed: "The static metrics file could not be loaded. The full comparison remains available in the table below.",
      state: "State metrics",
      boundaries: "Boundary matching",
      retention: "Editorial retention",
      balanced_accuracy: "Balanced accuracy",
      unknown_ratio: "UNKNOWN ratio",
      live_recall: "LIVE recall",
      dead_recall: "DEAD recall",
      start_matches: "START candidates matched",
      end_matches: "END candidates matched",
      matched_intervals: "Complete editorial intervals matched",
      precision: "Boundary-pair precision",
      recall: "Boundary-pair recall",
      editorial_live_lost_seconds: "Editorial LIVE time lost",
      editorial_dead_kept_seconds: "Editorial DEAD time kept",
      seconds: "s"
    },
    "zh-CN": {
      loading: "正在读取已归档的对照结果…",
      loadFailed: "无法读取静态指标文件。下方表格仍保留完整对照数据。",
      state: "状态指标",
      boundaries: "边界配对",
      retention: "编辑保留时长",
      balanced_accuracy: "平衡准确率",
      unknown_ratio: "UNKNOWN 比例",
      live_recall: "LIVE 召回率",
      dead_recall: "DEAD 召回率",
      start_matches: "START 候选命中",
      end_matches: "END 候选命中",
      matched_intervals: "完整编辑回合区间命中",
      precision: "边界配对精确率",
      recall: "边界配对召回率",
      editorial_live_lost_seconds: "编辑 LIVE 时长损失",
      editorial_dead_kept_seconds: "编辑 DEAD 保留时长",
      seconds: "秒"
    }
  }[language];

  const groups = {
    state: ["balanced_accuracy", "unknown_ratio", "live_recall", "dead_recall"],
    boundaries: ["start_matches", "end_matches", "matched_intervals", "precision", "recall"],
    retention: ["editorial_live_lost_seconds", "editorial_dead_kept_seconds"]
  };

  function formatMetric(key, value) {
    if (["balanced_accuracy", "unknown_ratio", "live_recall", "dead_recall", "precision", "recall"].includes(key)) {
      return `${(value * 100).toFixed(2)}%`;
    }
    if (key.endsWith("_seconds")) return `${Number(value).toFixed(2)} ${words.seconds}`;
    return String(value);
  }

  function setupStudyControls() {
    const armButtons = [...document.querySelectorAll("[data-arm-button]")];
    const viewButtons = [...document.querySelectorAll("[data-metric-view]")];
    const valueNodes = [...document.querySelectorAll("[data-study-value]")];
    const heading = document.querySelector("[data-study-name]");
    const status = document.querySelector("[data-study-status]");
    const tableRows = [...document.querySelectorAll("[data-study-row]")];
    const panels = [...document.querySelectorAll("[data-metric-panel]")];
    if (!armButtons.length || !viewButtons.length || !heading || !status) return;

    let arms = [];
    let activeArm = "tail-safe";
    let activeView = "state";

    function render() {
      const selected = arms.find((arm) => arm.id === activeArm);
      if (!selected) return;
      heading.textContent = selected.label[language];
      status.textContent = `${selected.name} · ${words[activeView]}`;
      armButtons.forEach((button) => {
        button.setAttribute("aria-pressed", String(button.dataset.armButton === activeArm));
      });
      viewButtons.forEach((button) => {
        button.setAttribute("aria-pressed", String(button.dataset.metricView === activeView));
      });
      panels.forEach((panel) => {
        panel.hidden = panel.dataset.metricPanel !== activeView;
      });
      valueNodes.forEach((node) => {
        const key = node.dataset.studyValue;
        if (Object.hasOwn(selected, key)) node.textContent = formatMetric(key, selected[key]);
      });
      tableRows.forEach((row) => {
        row.classList.toggle("is-selected", row.dataset.studyRow === activeArm);
      });
    }

    armButtons.forEach((button) => {
      button.addEventListener("click", () => {
        activeArm = button.dataset.armButton;
        render();
      });
    });
    viewButtons.forEach((button) => {
      button.addEventListener("click", () => {
        activeView = button.dataset.metricView;
        render();
      });
    });

    const root = document.body.dataset.siteRoot || "./";
    const dataUrl = new URL(`${root}research-metrics.json`, document.baseURI);
    fetch(dataUrl, { credentials: "omit" })
      .then((response) => {
        if (!response.ok) throw new Error("static metrics response was not successful");
        return response.json();
      })
      .then((payload) => {
        if (payload.schema_version !== "badminton-offline-study-metrics-v1" || !Array.isArray(payload.arms)) {
          throw new Error("unknown archived metrics schema");
        }
        arms = payload.arms;
        render();
        status.setAttribute("data-ready", "true");
      })
      .catch(() => {
        status.textContent = words.loadFailed;
      });
  }

  function setupImageDialog() {
    const dialog = document.querySelector("#image-dialog");
    const fullImage = dialog && dialog.querySelector("img");
    if (!dialog || !fullImage || typeof dialog.showModal !== "function") return;

    document.querySelectorAll("[data-zoom]").forEach((link) => {
      link.addEventListener("click", (event) => {
        event.preventDefault();
        const thumbnail = link.querySelector("img");
        fullImage.src = link.href;
        fullImage.alt = thumbnail ? thumbnail.alt : "";
        dialog.showModal();
      });
    });
    dialog.querySelector("[data-dialog-close]").addEventListener("click", () => dialog.close());
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });
  }

  setupStudyControls();
  setupImageDialog();
})();
