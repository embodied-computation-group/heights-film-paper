/**
 * jsPsych 8 plugin: place a dot on a valence x arousal grid for a short scenario,
 * using the same pointer-locked mouse "joystick" as the film rating, then get
 * feedback on the expected quadrant. Used to practise telling apart e.g.
 * unpleasant/activated from unpleasant/calm states before the film.
 *
 * Correct = dot in the expected quadrant, at least `dead_zone` units from both
 * midlines. Space confirms. Esc releases the mouse (click to continue).
 */
var jsPsychAffectPlacement = (function (jspsych) {
  "use strict";

  const PT = jspsych.ParameterType;

  const info = {
    name: "affect-placement",
    version: "0.1.0",
    parameters: {
      scenario: { type: PT.HTML_STRING, default: "" },
      /** Expected quadrant: valence "neg"|"pos", arousal "low"|"high". */
      expected: { type: PT.OBJECT, default: { valence: "neg", arousal: "high" } },
      /** Explanation shown in the feedback. */
      explanation: { type: PT.HTML_STRING, default: "" },
      x_low_label: { type: PT.STRING, default: "Unpleasant" },
      x_high_label: { type: PT.STRING, default: "Pleasant" },
      low_label: { type: PT.STRING, default: "Calm" },
      high_label: { type: PT.STRING, default: "Activated" },
      dead_zone: { type: PT.FLOAT, default: 5 },
      joystick_full_scale_frac: { type: PT.FLOAT, default: 0.6 },
      joystick_max_step_px: { type: PT.FLOAT, default: 150 },
    },
    data: {
      scenario: { type: PT.HTML_STRING },
      expected_valence: { type: PT.STRING },
      expected_arousal: { type: PT.STRING },
      x: { type: PT.FLOAT },
      y: { type: PT.FLOAT },
      correct: { type: PT.BOOL },
      rt: { type: PT.FLOAT },
      trajectory: { type: PT.COMPLEX },
    },
  };

  const clamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));
  const r1 = (x) => Math.round(x * 10) / 10;

  class AffectPlacementPlugin {
    static info = info;

    constructor(jsPsych) {
      this.jsPsych = jsPsych;
    }

    trial(display_element, trial) {
      const px = Math.round(screen.height * trial.joystick_full_scale_frac);
      const exp = trial.expected;
      display_element.innerHTML = `
        <div class="ap-wrap">
          <div class="ap-scenario">${trial.scenario}</div>
          <div class="ap-area">
            <span class="cr-grid-label ap-top">${trial.high_label}</span>
            <span class="cr-grid-label ap-bottom">${trial.low_label}</span>
            <span class="cr-grid-label ap-left">${trial.x_low_label}</span>
            <span class="cr-grid-label ap-right">${trial.x_high_label}</span>
            <div class="ap-box">
              <div class="ap-quad" hidden></div>
              <div class="cr-grid-h"></div><div class="cr-grid-v"></div>
              <div class="cr-grid-dot ap-dot"></div>
            </div>
          </div>
          <div class="ap-msg">Click the box, then move the mouse to place the dot. Press <b>SPACE</b> to confirm.</div>
          <div class="ap-feedback" hidden></div>
          <button class="jspsych-btn ap-next" hidden>Next</button>
        </div>`;

      const $ = (s) => display_element.querySelector(s);
      const area = $(".ap-area");
      const dot = $(".ap-dot");
      const msg = $(".ap-msg");
      let x = 50;
      let y = 50;
      let moved = false;
      let done = false;
      let skipNext = false;
      const t0 = performance.now();
      const traj = [];

      const render = () => {
        dot.style.left = `${x}%`;
        dot.style.bottom = `${y}%`;
      };
      render();

      const locked = () => document.pointerLockElement === area;
      const lock = async () => {
        skipNext = true;
        try {
          const p = area.requestPointerLock();
          if (p && p.then) await p;
        } catch (e) {
          /* user can click again */
        }
      };
      area.addEventListener("click", () => {
        if (!done && !locked()) lock();
      });

      const onMove = (ev) => {
        if (done || !locked()) return;
        if (skipNext) {
          skipNext = false;
          return;
        }
        const lim = trial.joystick_max_step_px;
        x = clamp(x + (clamp(ev.movementX, -lim, lim) * 100) / px, 0, 100);
        y = clamp(y - (clamp(ev.movementY, -lim, lim) * 100) / px, 0, 100);
        moved = true;
        traj.push([r1(performance.now() - t0), r1(x), r1(y)]);
        render();
      };
      const onLock = () => {
        msg.innerHTML = locked()
          ? "Move the mouse to place the dot. Press <b>SPACE</b> to confirm."
          : "Click the box, then move the mouse to place the dot. Press <b>SPACE</b> to confirm.";
      };
      const onKey = (ev) => {
        if (ev.code !== "Space" || done) return;
        ev.preventDefault();
        if (!moved) return;
        confirm();
      };
      document.addEventListener("mousemove", onMove);
      document.addEventListener("pointerlockchange", onLock);
      document.addEventListener("keydown", onKey);

      const confirm = () => {
        done = true;
        const rt = performance.now() - t0;
        if (locked()) document.exitPointerLock();
        const dz = trial.dead_zone;
        const vOk = exp.valence === "neg" ? x < 50 - dz : x > 50 + dz;
        const aOk = exp.arousal === "high" ? y > 50 + dz : y < 50 - dz;
        const correct = vOk && aOk;

        const quad = $(".ap-quad");
        quad.style.left = exp.valence === "neg" ? "0" : "50%";
        quad.style.bottom = exp.arousal === "high" ? "50%" : "0";
        quad.hidden = false;
        msg.hidden = true;
        const where = `${exp.arousal === "high" ? "upper" : "lower"}-${exp.valence === "neg" ? "left" : "right"}`;
        const fb = $(".ap-feedback");
        fb.innerHTML = correct
          ? `<p><b>Yes &ndash; that fits.</b> This is usually placed in the <b>${where}</b> area (highlighted). ${trial.explanation}</p>`
          : `<p><b>Most people would place this in the ${where} area</b> (highlighted). ${trial.explanation}</p>`;
        fb.hidden = false;
        const next = $(".ap-next");
        next.hidden = false;
        next.addEventListener("click", () => {
          document.removeEventListener("mousemove", onMove);
          document.removeEventListener("pointerlockchange", onLock);
          document.removeEventListener("keydown", onKey);
          display_element.innerHTML = "";
          this.jsPsych.finishTrial({
            scenario: trial.scenario,
            expected_valence: exp.valence,
            expected_arousal: exp.arousal,
            x: r1(x),
            y: r1(y),
            correct,
            rt: Math.round(rt),
            trajectory: traj,
          });
        });
      };
    }
  }

  return AffectPlacementPlugin;
})(jsPsychModule);
