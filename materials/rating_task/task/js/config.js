/**
 * Study configuration. Anything here can be overridden without redeploying by
 * putting the same keys in the JATOS study properties -> "Study input" (JSON).
 */
var CONFIG = {
  /** Film URL on JATOS: a file in the study assets folder, or a full https URL. */
  videoUrl: "towerClimb_crf29.mp4",
  /** Film URL when running locally (scripts/serve_local.sh serves the repo root). */
  localVideoUrl: "../media/towerClimb_crf29.mp4",
  filmLengthText: "about 13½ minutes",
  /**
   * Download the whole film in the background (after consent + device check) and play it from memory,
   * so playback never buffers. If it is not ready at the film, a progress page waits for it; after
   * preloadMaxWaitMs of waiting (or on error): if returnOnSlowDownload, the study ends and the participant is
   * asked to return it (code VMPSLOWD); otherwise the film is streamed from videoUrl instead.
   */
  preload: true,
  preloadMaxWaitMs: 5 * 60 * 1000,
  returnOnSlowDownload: true,
  /** The film is played muted, as it was in the fMRI session. */
  muted: true,

  /** "joystick" (pointer-locked mouse, overlay inside the film frame) or "slider" (1D only). URL ?input= overrides. */
  inputMode: "joystick",
  /** Joystick: mouse travel for the full scale, as a fraction of screen height. */
  joystickFullScaleFrac: 0.6,
  /** After a reload, resume the film this many seconds before the last saved position. */
  resumeRewindSeconds: 5,

  sampleRateHz: 20,
  chunkSeconds: 30,

  /** Practice must reach this mean absolute error (0-100 scale) or it is repeated once. */
  practiceMaxMae: 15,
  /** 2D practice: mean Euclidean distance threshold (0-100 units). */
  practiceMaxErr2D: 20,
  /** 2D practice path [t, x, y]: the four corners, the centre, then a diagonal glide. */
  practiceKeyframes2D: [
    [0, 20, 20], [6, 20, 20],
    [6, 80, 80], [12, 80, 80],
    [12, 20, 80], [18, 20, 80],
    [18, 80, 20], [24, 80, 20],
    [24, 50, 50], [28, 50, 50],
    [36, 90, 65], [40, 90, 65],
  ],
  practiceKeyframes: [
    [0, 15], [7, 15],
    [7, 85], [14, 85],
    [14, 50], [19, 50],
    [29, 95], [34, 95],
    [34, 30], [40, 30],
  ],

  minScreen: { width: 1000, height: 600 },

  prolific: {
    completeUrl: "https://app.prolific.com/submissions/complete?cc=VMPDONE1",
    noConsentUrl: "https://app.prolific.com/submissions/complete?cc=VMPNOCON",
    slowDownloadUrl: "https://app.prolific.com/submissions/complete?cc=VMPSLOWD",
  },

  /**
   * The two studies. Each Prolific study passes ?dim=<key> in its URL (each participant does one
   * study only); without it, one is chosen at random from `assignable`.
   *   anxiety  - Study 1: continuous 1D anxiety rating (vertical bar overlay)
   *   affect2d - Study 2: continuous 2D valence x arousal grid (Affect-Grid style; x = valence, y = arousal)
   */
  assignable: ["anxiety", "affect2d"],
  dimensions: {
    anxiety: {
      study: 1,
      label: "how tense or anxious you felt",
      question: "How <b>tense or anxious</b> do you feel right now?",
      low: "Not at all",
      high: "Extremely",
      start: 0,
      note: "This is about your own feelings while watching, including feeling anxious for the people on screen.",
    },
    affect2d: {
      study: 2,
      axes: 2,
      label: "how pleasant or unpleasant and how activated you felt",
      question: "How do you feel right now? <b>Left&ndash;right:</b> unpleasant&ndash;pleasant. <b>Down&ndash;up:</b> low&ndash;high activation.",
      xLow: "Unpleasant",
      xHigh: "Pleasant",
      low: "Low activation",
      high: "High activation",
      start: 50,
      startX: 50,
      note: "Left&ndash;right shows how unpleasant or pleasant you feel (neutral in the centre). Down&ndash;up shows how activated you feel: feeling activated or stirred up, regardless of whether the feeling is pleasant or unpleasant.",
    },
  },
};
