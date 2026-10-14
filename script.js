"use strict";

// Published values: arXiv:2608.02365v2, Tables 1–2 and Appendix G.
const benchmarks = {
  robotwin: {
    name: "RoboTwin 2.0",
    latency: [53.2, 71.2, 196.8],
    speedup: "3.7×",
    success: "90.5 ± 0.2%",
  },
  libero: {
    name: "LIBERO",
    latency: [52.0, 67.7, 196.0],
    speedup: "3.8×",
    success: "98.3 ± 0.1%",
  },
};

const benchmarkButtons = document.querySelectorAll("[data-benchmark]");
benchmarkButtons.forEach((button) =>
  button.addEventListener("click", () => {
    const data = benchmarks[button.dataset.benchmark];
    benchmarkButtons.forEach((other) =>
      other.setAttribute("aria-pressed", String(other === button)),
    );
    document.querySelector("#latency-chart-title").textContent =
      `${data.name} · model computation per action chunk`;
    document.querySelectorAll("#latency-bars .bar-row").forEach((row, i) => {
      row.querySelector(".bar-track > span").style.width =
        `${(data.latency[i] / data.latency[2]) * 100}%`;
      row
        .querySelector("strong")
        .replaceChildren(
          document.createTextNode(`${data.latency[i].toFixed(1)} `),
          Object.assign(document.createElement("small"), { textContent: "ms" }),
        );
    });
    document.querySelector("#latency-axis-end").textContent =
      `${data.latency[2].toFixed(1)} ms`;
    document.querySelector("#speedup-value").textContent = data.speedup;
    document.querySelector("#success-value").textContent = data.success;
    document.querySelector("#success-label").textContent =
      `average success on ${data.name}`;
  }),
);

// The slider and playback clock use elapsed seconds. Sparse recorded images are
// held until the next sample; completion times come from Appendix G.
const snapshotTimes = [
  ...Array.from({ length: 29 }, (_, index) => index * 5),
  21,
].sort((a, b) => a - b);
const policies = {
  fasterwam: { label: "Faster-WAM", end: 21.2, finalSnapshot: 25 },
  pi05: { label: "Pi 0.5", end: 21.6, finalSnapshot: 25 },
  fastwam: { label: "Fast-WAM", end: 38.5, finalSnapshot: 40 },
  lingbot: { label: "LingBot-VA", end: 139.9, finalSnapshot: 140 },
};
const slider = document.querySelector("#rollout-time");
const previous = document.querySelector("#previous-frame");
const next = document.querySelector("#next-frame");
const playButton = document.querySelector("#play-rollout");
const playbackRateButtons = document.querySelectorAll("[data-playback-rate]");
const duration = Number(slider.max);
let playbackRate = 1;
let playing = false;
let animation = null;
let startedAt = 0;
let startTime = 0;

function updatePlayButton() {
  const atEnd = Number(slider.value) >= duration;
  playButton.textContent = playing
    ? `Pause · ${playbackRate}×`
    : atEnd
      ? `Replay · ${playbackRate}×`
      : `Play · ${playbackRate}×`;
  playButton.setAttribute("aria-pressed", String(playing));
  playButton.setAttribute(
    "aria-label",
    playing
      ? "Pause rollout comparison"
      : `${atEnd ? "Replay" : "Play"} rollout comparison at ${playbackRate}× speed`,
  );
}

function updateSnapshot() {
  const time = Number(slider.value);
  document.querySelector("#time-label").textContent = `${time.toFixed(1)} s`;
  slider.setAttribute("aria-valuetext", `${time.toFixed(1)} seconds`);
  previous.disabled = time <= 0;
  next.disabled = time >= duration;
  const sampledTime = snapshotTimes.filter((sample) => sample <= time).at(-1);
  document.querySelectorAll("[data-policy]").forEach((card) => {
    const key = card.dataset.policy;
    const policy = policies[key];
    const complete = time >= policy.end;
    const frame = complete ? policy.finalSnapshot : sampledTime;
    const img = card.querySelector("img");
    if (img.dataset.frame !== String(frame)) {
      img.src = `assets/rollouts/${key}/${String(frame).padStart(3, "0")}s.webp`;
      img.dataset.frame = String(frame);
      img.alt = `${policy.label} pick-fruit rollout: ${complete ? "task complete, final recorded frame" : `recorded at ${frame} seconds`}`;
    }
    card.classList.toggle("complete", complete);
    card.querySelector(".rollout-state").textContent = complete
      ? "Task complete"
      : "In progress";
    card.querySelector(".frame-note").textContent = complete
      ? "Final recorded frame held"
      : `Recorded at ${frame} s${time > frame ? " · frame held" : ""}`;
  });
  updatePlayButton();
}

function pausePlayback() {
  playing = false;
  cancelAnimationFrame(animation);
  animation = null;
  updatePlayButton();
}

function playbackTime(now) {
  return Math.min(
    duration,
    startTime + ((now - startedAt) / 1000) * playbackRate,
  );
}

function tick(now) {
  if (!playing) return;
  const time = playbackTime(now);
  slider.value = time.toFixed(1);
  updateSnapshot();
  if (time >= duration) {
    pausePlayback();
  } else {
    animation = requestAnimationFrame(tick);
  }
}

playButton.addEventListener("click", () => {
  if (playing) {
    pausePlayback();
    return;
  }
  if (Number(slider.value) >= duration) slider.value = "0";
  startTime = Number(slider.value);
  startedAt = performance.now();
  playing = true;
  updateSnapshot();
  animation = requestAnimationFrame(tick);
});
playbackRateButtons.forEach((button) => {
  button.addEventListener("click", () => {
    // Anchor the new rate at the current recorded time to avoid a seek or reset.
    if (playing) {
      const now = performance.now();
      startTime = playbackTime(now);
      startedAt = now;
      slider.value = startTime.toFixed(1);
    }
    playbackRate = Number(button.dataset.playbackRate);
    playbackRateButtons.forEach((other) =>
      other.setAttribute("aria-pressed", String(other === button)),
    );
    document.querySelector("#playback-rate-note").textContent =
      `1 second of playback = ${playbackRate} second${playbackRate === 1 ? "" : "s"} of recorded time`;
    if (Number(slider.value) >= duration) pausePlayback();
    updateSnapshot();
  });
});
slider.addEventListener("input", () => {
  pausePlayback();
  updateSnapshot();
});
previous.addEventListener("click", () => {
  pausePlayback();
  slider.value =
    snapshotTimes.filter((time) => time < Number(slider.value)).at(-1) ?? 0;
  updateSnapshot();
});
next.addEventListener("click", () => {
  pausePlayback();
  slider.value =
    snapshotTimes.find((time) => time > Number(slider.value)) ?? duration;
  updateSnapshot();
});
document.addEventListener("visibilitychange", () => {
  if (document.hidden) pausePlayback();
});
updateSnapshot();

const copyButton = document.querySelector("#copy-citation");
copyButton.addEventListener("click", async () => {
  const citation = document.querySelector("#bibtex");
  const status = document.querySelector("#copy-status");
  try {
    await navigator.clipboard.writeText(citation.textContent);
    copyButton.textContent = "Copied ✓";
    status.textContent = "BibTeX copied to clipboard.";
    setTimeout(() => {
      copyButton.textContent = "Copy BibTeX";
      status.textContent = "";
    }, 2500);
  } catch {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(citation);
    selection.removeAllRanges();
    selection.addRange(range);
    status.textContent =
      "BibTeX selected. Press Ctrl+C (or ⌘C on Mac) to copy.";
  }
});

document.querySelectorAll("[data-enhancement]").forEach((element) => {
  element.hidden = false;
});
