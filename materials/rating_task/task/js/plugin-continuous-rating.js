/**
 * jsPsych 8 plugin: continuous rating while a video plays (video_url) or while
 * following a moving target (practice_keyframes).
 *
 * Input modes
 *   "joystick": the pointer is locked and hidden (Pointer Lock API); vertical
 *               mouse movement moves the rating (position control, clamped to
 *               0-100, holds when the hand rests). Feedback is a small semi-transparent
 *               vertical bar in the lower-right corner of the video frame, so
 *               participants never look away from the film.
 *   "slider":   a drag slider under the video.
 *   Arrow keys adjust the value in both modes.
 *
 * Axes
 *   axes: 1  single scale (vertical bar / slider).
 *   axes: 2  2D grid (Affect-Grid style): horizontal mouse movement = x (x_low_label..x_high_label),
 *            vertical = y (low_label..high_label). Feedback is a small translucent grid with a dot
 *            in the lower-right corner of the frame. Joystick only.
 *
 * Every sample is stamped with the *stimulus clock* (video.currentTime, or the
 * practice clock, which only advances while running), the media time of the last
 * frame actually presented (requestVideoFrameCallback, video only), and wall-clock
 * time, so buffering stalls and pauses never misalign the rating series.
 *
 * Raw trajectory: every input event is logged with its resulting value(s) plus the
 * raw, unclamped mouse movement (dx, dy in px) and its source (m=mouse, k=key,
 * s=slider). Nothing is smoothed.
 *
 * Interruptions (tab hidden, fullscreen exit, pointer lock released with Esc)
 * pause the stimulus and show an overlay; the participant must click to resume.
 *
 * Data are streamed out every `chunk_seconds` through `on_chunk` (crash
 * backup) and also returned in full, column-wise, as trial data.
 */
var jsPsychContinuousRating = (function (jspsych) {
  "use strict";

  const PT = jspsych.ParameterType;

  const info = {
    name: "continuous-rating",
    version: "0.4.0",
    parameters: {
      /** Video to play. If null, runs in practice mode (needs practice_keyframes). */
      video_url: { type: PT.STRING, default: null },
      /** Play the video without sound. */
      muted: { type: PT.BOOL, default: false },
      /** Start the video at this time (seconds): used to resume after a reload, and for testing. */
      start_time: { type: PT.FLOAT, default: 0 },
      /** Practice target path: [[t_seconds, value_0_100], ...]; repeat a time for a step change. */
      practice_keyframes: { type: PT.COMPLEX, default: null },
      /** Seconds to skip at start (and after jumps) when scoring practice tracking error. */
      practice_grace: { type: PT.FLOAT, default: 1.5 },
      /** "joystick" or "slider". */
      input_mode: { type: PT.STRING, default: "joystick" },
      /** 1 = single scale, 2 = 2D grid (forces joystick). Practice keyframes then are [t, x, y]. */
      axes: { type: PT.INT, default: 1 },
      x_low_label: { type: PT.STRING, default: "" },
      x_high_label: { type: PT.STRING, default: "" },
      start_value_x: { type: PT.FLOAT, default: 50 },
      /** Joystick: mouse travel for the full 0-100 range, as a fraction of screen height. */
      joystick_full_scale_frac: { type: PT.FLOAT, default: 0.6 },
      /** Joystick: per-event movement clamp (px), guards against pointer-lock jump glitches. */
      joystick_max_step_px: { type: PT.FLOAT, default: 150 },
      question: { type: PT.HTML_STRING, default: "" },
      low_label: { type: PT.STRING, default: "" },
      mid_label: { type: PT.STRING, default: "" },
      high_label: { type: PT.STRING, default: "" },
      start_value: { type: PT.FLOAT, default: 50 },
      /** Participant sets a baseline before the stimulus starts (slider: must move it; joystick: Space to start). */
      require_initial_set: { type: PT.BOOL, default: true },
      start_prompt: { type: PT.HTML_STRING, default: "" },
      start_button_label: { type: PT.STRING, default: "Start" },
      /** Joystick: banner shown while setting the baseline. */
      arming_prompt: {
        type: PT.HTML_STRING,
        default: "Move the mouse up or down to show how you feel <b>right now</b>.<br>Then press <b>SPACE</b> to start.",
      },
      sample_rate_hz: { type: PT.INT, default: 20 },
      chunk_seconds: { type: PT.FLOAT, default: 30 },
      /** Called with {tag, chunk, samples, inputs, events} every chunk_seconds and at the end. */
      on_chunk: { type: PT.FUNCTION, default: null },
      tag: { type: PT.STRING, default: "rating" },
      require_fullscreen: { type: PT.BOOL, default: true },
      key_step: { type: PT.FLOAT, default: 2 },
    },
    data: {
      tag: { type: PT.STRING },
      mode: { type: PT.STRING },
      input_mode: { type: PT.STRING },
      axes: { type: PT.INT },
      joystick_px_full_scale: { type: PT.FLOAT },
      start_time: { type: PT.FLOAT },
      initial_value: { type: PT.FLOAT },
      stimulus_duration: { type: PT.FLOAT },
      /** Column-wise: t_stim, t_frame (video), t_wall, value | value_x+value_y, playing, target(s) (practice). */
      samples: { type: PT.COMPLEX },
      inputs: { type: PT.COMPLEX },
      events: { type: PT.COMPLEX },
      n_interruptions: { type: PT.INT },
      interrupted_ms: { type: PT.FLOAT },
      n_stalls: { type: PT.INT },
      stalled_ms: { type: PT.FLOAT },
      wall_duration_ms: { type: PT.FLOAT },
      practice_mae: { type: PT.FLOAT },
    },
  };

  const r3 = (x) => Math.round(x * 1000) / 1000;
  const r1 = (x) => Math.round(x * 10) / 10;
  const clamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));

  function targetAt(kf, t) {
    let i = 0;
    for (let k = 0; k < kf.length; k++) if (kf[k][0] <= t) i = k;
    const a = kf[i];
    const b = kf[i + 1];
    const out = [];
    for (let j = 1; j < a.length; j++) {
      out.push(!b || b[0] <= a[0] ? a[j] : a[j] + ((b[j] - a[j]) * (t - a[0])) / (b[0] - a[0]));
    }
    return out;
  }

  class ContinuousRatingPlugin {
    static info = info;

    constructor(jsPsych) {
      this.jsPsych = jsPsych;
    }

    trial(display_element, trial) {
      const isVideo = !!trial.video_url;
      const is2D = trial.axes === 2;
      const isJoy = trial.input_mode === "joystick" || is2D;
      if (!isVideo && !trial.practice_keyframes) {
        throw new Error("continuous-rating: need video_url or practice_keyframes");
      }
      const kf = trial.practice_keyframes;
      const practiceDuration = isVideo ? null : kf[kf.length - 1][0];
      const bipolar = !!trial.mid_label;
      const pxFullScale = Math.round(screen.height * trial.joystick_full_scale_frac);

      display_element.innerHTML = `
        <div class="cr-wrap ${isJoy ? "cr-joy" : "cr-sl"}">
          ${isJoy ? `<div class="cr-question-top">${trial.question}</div>` : ""}
          <div class="cr-stage">
            ${isVideo
              ? `<video class="cr-video cr-media" playsinline preload="auto" disablepictureinpicture
                   controlslist="nodownload noplaybackrate noremoteplayback"></video>`
              : `<div class="cr-practice cr-media"><p class="cr-practice-msg">${
                  is2D
                    ? "Keep the white dot on the orange marker."
                    : isJoy
                      ? "Keep the white bar level with the orange marker."
                      : "Keep the slider on the orange marker."
                }</p></div>`}
            ${is2D
              ? `<div class="cr-grid" hidden>
                   <span class="cr-grid-label cr-grid-top">${trial.high_label}</span>
                   <span class="cr-grid-label cr-grid-bottom">${trial.low_label}</span>
                   <span class="cr-grid-label cr-grid-left">${trial.x_low_label}</span>
                   <span class="cr-grid-label cr-grid-right">${trial.x_high_label}</span>
                   <div class="cr-grid-box">
                     <div class="cr-grid-h"></div><div class="cr-grid-v"></div>
                     <div class="cr-grid-target" hidden></div>
                     <div class="cr-grid-dot"></div>
                   </div>
                 </div>
                 <div class="cr-banner" hidden></div>`
              : isJoy
              ? `<div class="cr-bar" hidden>
                   <span class="cr-bar-label cr-bar-high">${trial.high_label}</span>
                   ${bipolar ? `<span class="cr-bar-label cr-bar-midlabel">${trial.mid_label}</span>` : ""}
                   <span class="cr-bar-label cr-bar-low">${trial.low_label}</span>
                   <div class="cr-bar-track">
                     ${bipolar ? `<div class="cr-bar-mid"></div>` : ""}
                     <div class="cr-bar-fill"></div>
                     <div class="cr-bar-level"></div>
                     <div class="cr-bar-target" hidden></div>
                   </div>
                 </div>
                 <div class="cr-banner" hidden></div>`
              : ""}
            <div class="cr-overlay">
              <div class="cr-overlay-box">
                <div class="cr-overlay-msg"></div>
                <button class="jspsych-btn cr-overlay-btn" disabled>${trial.start_button_label}</button>
              </div>
            </div>
          </div>
          ${isJoy
            ? ""
            : `<div class="cr-panel">
                <div class="cr-question">${trial.question}</div>
                <div class="cr-scale">
                  <span class="cr-label cr-low">${trial.low_label}</span>
                  <div class="cr-track">
                    <input type="range" class="cr-slider" min="0" max="100" step="0.5"
                           value="${trial.start_value}" aria-label="rating">
                    ${bipolar ? `<div class="cr-mid"><span>${trial.mid_label}</span></div>` : ""}
                    <div class="cr-target" hidden></div>
                  </div>
                  <span class="cr-label cr-high">${trial.high_label}</span>
                </div>
              </div>`}
        </div>`;

      const $ = (s) => display_element.querySelector(s);
      const stage = $(".cr-stage");
      const media = $(".cr-media");
      const video = $(".cr-video");
      const slider = $(".cr-slider");
      const overlay = $(".cr-overlay");
      const overlayMsg = $(".cr-overlay-msg");
      const overlayBtn = $(".cr-overlay-btn");
      const bar = is2D ? $(".cr-grid") : $(".cr-bar");
      const banner = $(".cr-banner");
      const target = is2D ? $(".cr-grid-target") : isJoy ? $(".cr-bar-target") : $(".cr-target");

      // ---- state ---------------------------------------------------------
      // phase: loading -> ready -> [arming] -> running <-> interrupted -> done
      let phase = "loading";
      let resumeTo = null;
      let val = clamp(trial.start_value, 0, 100); // y (or the single value)
      let valX = clamp(trial.start_value_x, 0, 100); // x, 2D only
      let touched = !trial.require_initial_set;
      let initialValue = null;
      const t0 = performance.now();
      const wall = () => performance.now() - t0;
      let running = false; // stimulus clock advancing
      let practiceElapsed = 0; // seconds, accumulated only while running
      let practiceLastTick = null;
      let interruptStart = null;
      let stallStart = null;
      let sampler = null;
      let lastFrameTime = null; // media time of the last presented frame (video only)
      let chunker = null;
      const stats = {
        n_interruptions: 0,
        interrupted_ms: 0,
        n_stalls: 0,
        stalled_ms: 0,
        n_untrusted_events: 0, // input events generated by script (isTrusted false) - evidence of automation
        max_mouse_step_px: 0, // largest single raw mouse movement (unclamped)
      };

      const all = { samples: [], inputs: [], events: [] };
      let buf = { samples: [], inputs: [], events: [] };
      let chunkIdx = 0;

      const stimTime = () => {
        if (isVideo) return video.currentTime;
        if (running && practiceLastTick !== null) {
          return practiceElapsed + (performance.now() - practiceLastTick) / 1000;
        }
        return practiceElapsed;
      };
      const push = (kind, row) => {
        all[kind].push(row);
        buf[kind].push(row);
      };
      const logEvent = (e, extra) =>
        push("events", Object.assign({ e, t_stim: r3(stimTime()), t_wall: r1(wall()) }, extra || {}));

      const flush = () => {
        if (typeof trial.on_chunk === "function") {
          try {
            trial.on_chunk({ tag: trial.tag, chunk: chunkIdx, ...buf });
          } catch (err) {
            console.error(err);
          }
        }
        chunkIdx++;
        buf = { samples: [], inputs: [], events: [] };
      };

      // ---- value + display -----------------------------------------------
      const pct = (v) => `${v}%`;
      const render = () => {
        if (!isJoy) {
          slider.value = val;
          return;
        }
        if (is2D) {
          const dot = $(".cr-grid-dot");
          dot.style.left = pct(valX);
          dot.style.bottom = pct(val);
          return;
        }
        const origin = bipolar ? 50 : 0;
        const lo = Math.min(val, origin);
        const hi = Math.max(val, origin);
        const intensity = Math.abs(val - origin) / (bipolar ? 50 : 100);
        const fill = $(".cr-bar-fill");
        fill.style.bottom = pct(lo);
        fill.style.height = pct(hi - lo);
        fill.style.opacity = 0.55 + 0.4 * intensity;
        $(".cr-bar-level").style.bottom = pct(val);
      };
      const setValue = (v, src, vx = valX, raw = [0, 0]) => {
        val = clamp(v, 0, 100);
        if (is2D) valX = clamp(vx, 0, 100);
        render();
        if (!touched) {
          touched = true;
          if (phase === "ready" && !isJoy) overlayBtn.disabled = false;
        }
        const vals = is2D ? [r1(valX), r1(val)] : [r1(val)];
        push("inputs", [r3(stimTime()), r1(wall()), ...vals, src[0], raw[0], raw[1]]);
      };
      render();

      // Joystick bar sits inside the right edge of the displayed video/practice frame.
      const placeBar = () => {
        if (!bar) return;
        const s = stage.getBoundingClientRect();
        const m = media.getBoundingClientRect();
        if (!m.width || !m.height) return;
        if (is2D) {
          // Lower-right corner, leaving room for the right/bottom labels.
          const size = Math.round(Math.min(m.height * 0.22, 170));
          bar.style.width = `${size}px`;
          bar.style.height = `${size}px`;
          bar.style.left = `${m.right - s.left - size - 90}px`;
          bar.style.top = `${m.bottom - s.top - size - 34}px`;
          bar.hidden = false;
          return;
        }
        // Small fixed bar in the lower-right corner (same region as the 2D grid), labels to its left.
        const h = Math.round(Math.min(m.height * 0.3, 220));
        bar.style.left = `${m.right - s.left - 14 - 40}px`;
        bar.style.top = `${m.bottom - s.top - h - 34}px`;
        bar.style.height = `${h}px`;
        bar.hidden = false;
      };
      window.addEventListener("resize", placeBar);

      // ---- inputs ----------------------------------------------------------
      if (slider) {
        slider.addEventListener("input", () => setValue(parseFloat(slider.value), "slider"));
      }
      // The first movement event after a (re)lock can carry a spurious jump; drop it.
      let skipNextMove = false;
      const onMouseMove = (ev) => {
        if (!ev.isTrusted) stats.n_untrusted_events++;
        // Check the lock directly: pointerlockchange can arrive after the first movements.
        if (document.pointerLockElement !== stage || (phase !== "running" && phase !== "arming")) return;
        if (skipNextMove) {
          skipNextMove = false;
          return;
        }
        stats.max_mouse_step_px = Math.max(stats.max_mouse_step_px, Math.hypot(ev.movementX, ev.movementY));
        const lim = trial.joystick_max_step_px;
        const dy = clamp(ev.movementY, -lim, lim);
        const dx = is2D ? clamp(ev.movementX, -lim, lim) : 0;
        if (dy !== 0 || dx !== 0) {
          setValue(val - (dy * 100) / pxFullScale, "mouse", valX + (dx * 100) / pxFullScale, [ev.movementX, ev.movementY]);
        }
      };
      const onKey = (ev) => {
        if (!ev.isTrusted) stats.n_untrusted_events++;
        if (phase === "arming" && ev.code === "Space") {
          ev.preventDefault();
          startRun();
          return;
        }
        const step = trial.key_step;
        let dy, dx;
        if (is2D) {
          dy = { ArrowUp: 1, ArrowDown: -1, PageUp: 5, PageDown: -5 }[ev.key] || 0;
          dx = { ArrowRight: 1, ArrowLeft: -1 }[ev.key] || 0;
        } else {
          dy = { ArrowUp: 1, ArrowRight: 1, ArrowDown: -1, ArrowLeft: -1, PageUp: 5, PageDown: -5 }[ev.key] || 0;
          dx = 0;
        }
        if ((!dy && !dx) || phase === "done") return;
        ev.preventDefault();
        if (phase === "running" || phase === "arming" || (!isJoy && phase === "ready")) {
          setValue(val + dy * step, "key", valX + dx * step);
        }
      };
      document.addEventListener("mousemove", onMouseMove);
      document.addEventListener("keydown", onKey);

      // ---- pointer lock / fullscreen -------------------------------------
      const requestLock = async () => {
        try {
          const p = stage.requestPointerLock();
          if (p && typeof p.then === "function") await p;
          else await new Promise((r) => setTimeout(r, 300));
        } catch (err) {
          logEvent("lock_failed", { msg: String(err) });
        }
        return document.pointerLockElement === stage;
      };
      const ensureFullscreen = async () => {
        if (!trial.require_fullscreen || document.fullscreenElement) return;
        try {
          await document.documentElement.requestFullscreen();
        } catch (err) {
          logEvent("fs_request_failed", { msg: String(err) });
        }
      };

      // ---- overlay / banner ------------------------------------------------
      const showOverlay = (html, label, enabled) => {
        overlayMsg.innerHTML = html;
        overlayBtn.textContent = label;
        overlayBtn.disabled = !enabled;
        overlay.hidden = false;
      };
      const hideOverlay = () => {
        overlay.hidden = true;
        if (slider) slider.focus({ preventScroll: true });
      };
      const showBanner = (html) => {
        if (!banner) return;
        banner.innerHTML = html;
        banner.hidden = !html;
      };

      // ---- stimulus control ------------------------------------------------
      const play = () => {
        running = true;
        if (isVideo) {
          video.play().catch((err) => {
            running = false;
            logEvent("play_rejected", { msg: String(err) });
            interrupt("play_rejected");
          });
        } else {
          practiceLastTick = performance.now();
        }
      };
      const pause = () => {
        if (!isVideo && running && practiceLastTick !== null) {
          practiceElapsed += (performance.now() - practiceLastTick) / 1000;
          practiceLastTick = null;
        }
        running = false;
        if (isVideo) video.pause();
      };

      const enterArming = () => {
        phase = "arming";
        logEvent("arming");
        showBanner(trial.arming_prompt);
      };

      const startRun = () => {
        phase = "running";
        showBanner("");
        initialValue = is2D ? [r1(valX), r1(val)] : r1(val);
        logEvent("start", { initial_value: initialValue });
        sampler = setInterval(sample, 1000 / trial.sample_rate_hz);
        chunker = setInterval(flush, trial.chunk_seconds * 1000);
        if (!isVideo) target.hidden = false;
        play();
      };

      const INTERRUPT_MSG = {
        fs_exit: "you left full-screen mode",
        hidden: "you switched away from this page",
        pointer_unlock: "the mouse was released (for example by pressing Esc)",
        play_rejected: "your browser stopped playback",
      };
      const interrupt = (reason) => {
        if (phase !== "running" && phase !== "arming") return;
        resumeTo = phase;
        if (phase === "running") pause();
        phase = "interrupted";
        showBanner("");
        interruptStart = performance.now();
        stats.n_interruptions++;
        logEvent("interrupt", { reason });
        const what = isVideo ? "The film is paused" : "The practice is paused";
        showOverlay(
          `<p>${what} because ${INTERRUPT_MSG[reason] || "of an interruption"}.</p>
           <p>Please stay on this page in full screen until the end.</p>`,
          "Continue",
          true
        );
      };

      overlayBtn.addEventListener("click", async () => {
        if (phase !== "ready" && phase !== "interrupted") return;
        overlayBtn.disabled = true;
        await ensureFullscreen();
        placeBar();
        skipNextMove = true;
        if (isJoy && !(await requestLock())) {
          showOverlay("<p>Please click the button to continue.</p>", "Continue", true);
          return;
        }
        hideOverlay();
        if (phase === "ready") {
          if (isJoy && trial.require_initial_set) enterArming();
          else startRun();
          return;
        }
        // resuming from an interruption
        stats.interrupted_ms += performance.now() - interruptStart;
        interruptStart = null;
        logEvent("resume");
        if (resumeTo === "arming") {
          enterArming();
        } else {
          phase = "running";
          play();
        }
      });

      const onVisibility = () => {
        logEvent(document.hidden ? "hidden" : "visible");
        if (document.hidden) interrupt("hidden");
      };
      const onFullscreen = () => {
        const fs = !!document.fullscreenElement;
        logEvent(fs ? "fs_enter" : "fs_exit");
        placeBar();
        if (!fs && trial.require_fullscreen) interrupt("fs_exit");
      };
      const onLockChange = () => {
        const locked = document.pointerLockElement === stage;
        logEvent(locked ? "lock" : "unlock");
        if (!locked) interrupt("pointer_unlock");
      };
      const onBlur = () => logEvent("blur");
      const onFocus = () => logEvent("focus");
      document.addEventListener("visibilitychange", onVisibility);
      document.addEventListener("fullscreenchange", onFullscreen);
      document.addEventListener("pointerlockchange", onLockChange);
      window.addEventListener("blur", onBlur);
      window.addEventListener("focus", onFocus);

      // ---- sampling ----------------------------------------------------------
      const sample = () => {
        const ts = stimTime();
        const playing = isVideo ? !video.paused && !video.ended && stallStart === null : running;
        const row = [r3(ts)];
        if (isVideo) row.push(lastFrameTime === null ? null : r3(lastFrameTime));
        row.push(r1(wall()));
        if (is2D) row.push(r1(valX));
        row.push(r1(val), playing ? 1 : 0);
        if (!isVideo) {
          const tv = targetAt(kf, ts);
          setTarget(tv);
          row.push(...tv.map(r1));
          if (ts >= practiceDuration) end();
        }
        push("samples", row);
      };

      function setTarget(tv) {
        if (is2D) {
          target.style.setProperty("--x", tv[0]);
          target.style.setProperty("--y", tv[1]);
        } else {
          target.style.setProperty("--v", tv[0]);
        }
      }

      // ---- video wiring ----------------------------------------------------
      const becomeReady = () => {
        if (phase !== "loading") return;
        phase = "ready";
        placeBar();
        showOverlay(trial.start_prompt, trial.start_button_label, isJoy || touched);
      };
      if (isVideo) {
        let lastGoodTime = trial.start_time;
        showOverlay("<p>Loading the film&hellip;</p><p class='cr-small'>This can take a moment.</p>", trial.start_button_label, false);
        video.addEventListener("loadedmetadata", () => {
          if (trial.start_time > 0) video.currentTime = trial.start_time;
          placeBar();
        }, { once: true });
        video.addEventListener("canplay", () => {
          if (phase === "loading") logEvent("can_play", { duration: video.duration });
          becomeReady();
        });
        video.addEventListener("waiting", () => {
          if (phase !== "running" || stallStart !== null) return;
          stallStart = performance.now();
          stats.n_stalls++;
          logEvent("stall");
        });
        video.addEventListener("playing", () => {
          if (stallStart !== null) {
            stats.stalled_ms += performance.now() - stallStart;
            stallStart = null;
            logEvent("stall_end");
          }
          logEvent("playing");
        });
        video.addEventListener("pause", () => logEvent("pause"));
        video.addEventListener("timeupdate", () => {
          if (!video.seeking) lastGoodTime = video.currentTime;
        });
        video.addEventListener("seeking", () => {
          if (Math.abs(video.currentTime - lastGoodTime) > 1) {
            logEvent("seek_blocked", { to: r3(video.currentTime) });
            video.currentTime = lastGoodTime;
          }
        });
        video.addEventListener("ended", () => {
          logEvent("ended");
          end();
        });
        video.addEventListener("error", () => {
          logEvent("video_error", { code: video.error ? video.error.code : null });
          showOverlay(
            "<p>Sorry, the film could not be loaded. Please check your connection and reload the page.</p>",
            trial.start_button_label,
            false
          );
        });
        video.addEventListener("contextmenu", (e) => e.preventDefault());
        if ("requestVideoFrameCallback" in HTMLVideoElement.prototype) {
          const onFrame = (_now, meta) => {
            lastFrameTime = meta.mediaTime;
            if (phase !== "done") video.requestVideoFrameCallback(onFrame);
          };
          video.requestVideoFrameCallback(onFrame);
        }
        video.muted = trial.muted;
        video.src = trial.video_url;
      } else {
        setTarget(targetAt(kf, 0));
        requestAnimationFrame(becomeReady);
      }

      // ---- end -----------------------------------------------------------
      const end = () => {
        if (phase === "done") return;
        phase = "done";
        pause();
        clearInterval(sampler);
        clearInterval(chunker);
        if (interruptStart !== null) stats.interrupted_ms += performance.now() - interruptStart;
        if (stallStart !== null) stats.stalled_ms += performance.now() - stallStart;
        logEvent("end");
        flush();

        document.removeEventListener("mousemove", onMouseMove);
        document.removeEventListener("keydown", onKey);
        document.removeEventListener("visibilitychange", onVisibility);
        document.removeEventListener("fullscreenchange", onFullscreen);
        document.removeEventListener("pointerlockchange", onLockChange);
        window.removeEventListener("resize", placeBar);
        window.removeEventListener("blur", onBlur);
        window.removeEventListener("focus", onFocus);
        const stimulusDuration = isVideo ? r3(video.duration || 0) : practiceDuration;
        // Release the pointer and wait for the browser to confirm before tearing the page down:
        // removing the locked element in the same tick can leave the cursor captured/hidden.
        const finish = () => {
          if (video) {
            video.removeAttribute("src");
            video.load();
          }

          // Column-wise samples are much more compact than row objects.
          const valueCols = is2D ? ["value_x", "value_y"] : ["value"];
          const targetCols = isVideo ? [] : is2D ? ["target_x", "target_y"] : ["target"];
          const cols = ["t_stim", ...(isVideo ? ["t_frame"] : []), "t_wall", ...valueCols, "playing", ...targetCols];
          const col = (name) => cols.indexOf(name);
          const samples = Object.fromEntries(cols.map((c, j) => [c, all.samples.map((r) => r[j])]));
          const inputCols = ["t_stim", "t_wall", ...valueCols, "src", "dx", "dy"];
          const inputs = Object.fromEntries(inputCols.map((c, j) => [c, all.inputs.map((r) => r[j])]));

          let practice_mae = null;
          if (!isVideo) {
            const jumps = kf.filter((p, i) => i > 0 && kf[i - 1][0] === p[0]).map((p) => p[0]);
            // Mean absolute error (1D) or mean Euclidean distance (2D), 0-100 units.
            const err = is2D
              ? (r) => Math.hypot(r[col("value_x")] - r[col("target_x")], r[col("value_y")] - r[col("target_y")])
              : (r) => Math.abs(r[col("value")] - r[col("target")]);
            const errs = all.samples
              .filter((r) => r[col("playing")] === 1 && r[0] >= trial.practice_grace)
              .filter((r) => !jumps.some((j) => r[0] >= j && r[0] < j + trial.practice_grace))
              .map(err);
            practice_mae = errs.length ? r1(errs.reduce((a, b) => a + b, 0) / errs.length) : null;
          }

          display_element.innerHTML = "";
          this.jsPsych.finishTrial({
            tag: trial.tag,
            mode: isVideo ? "video" : "practice",
            input_mode: isJoy ? "joystick" : "slider",
            axes: is2D ? 2 : 1,
            joystick_px_full_scale: isJoy ? pxFullScale : null,
            start_time: trial.start_time,
            initial_value: initialValue,
            stimulus_duration: stimulusDuration,
            samples,
            inputs,
            events: all.events,
            ...stats,
            interrupted_ms: Math.round(stats.interrupted_ms),
          max_mouse_step_px: Math.round(stats.max_mouse_step_px),
            stalled_ms: Math.round(stats.stalled_ms),
            wall_duration_ms: Math.round(wall()),
            practice_mae,
          });
        };
        if (document.pointerLockElement) {
          let finished = false;
          const go = () => {
            if (finished) return;
            finished = true;
            document.removeEventListener("pointerlockchange", go);
            finish();
          };
          document.addEventListener("pointerlockchange", go);
          setTimeout(go, 600);
          document.exitPointerLock();
        } else {
          finish();
        }
      };
    }
  }

  return ContinuousRatingPlugin;
})(jsPsychModule);
