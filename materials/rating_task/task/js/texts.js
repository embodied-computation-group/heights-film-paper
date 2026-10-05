/**
 * All participant-facing statements in one place for ethics review:
 * participant information + consent, data protection, content note, debrief,
 * exclusion/no-consent messages.
 *
 * No ethics approval line: survey studies like this need no ethics review in Denmark
 * (Aarhus University standard waiver, confirmed by PI 2026-10-04).
 */
var STUDY_INFO = {
  title: "Feelings while watching a film",
  institution: "Center of Functionally Integrative Neuroscience (CFIN), Aarhus University, Denmark",
  piName: "Micah Allen",
  contactEmail: "micah@cfin.au.dk",
  dataController: "Aarhus University, Nordre Ringgade 1, 8000 Aarhus C, Denmark (CVR 31119103)",
  dpoEmail: "dpo@au.dk",
  duration: "about 30 minutes",
  payment: "£4.80",
};

var TEXTS = {
  /** Shown before consent. `cfg` = CONFIG. */
  information: (cfg) => {
    const s = STUDY_INFO;
    return `
    <h2>${s.title}</h2>
    <p class="muted">Participant information. Please read carefully before deciding whether to take part.</p>

    <h3>Who is doing this research?</h3>
    <p>This study is run by ${s.piName} and colleagues at the ${s.institution}.</p>

    <h3>What is the study about?</h3>
    <p>We want to understand how people's feelings change from moment to moment while they watch a film.
    The ratings you give will be combined with those of other participants to describe how the film is
    experienced over time, and used to help analyse brain imaging data collected from other people
    who watched the same film.</p>

    <h3>What will I do?</h3>
    <ul>
      <li>Answer two short questions and do a short practice of the rating method.</li>
      <li>Answer a short questionnaire about how you feel right now, both before and after the film.</li>
      <li>Watch a film of ${cfg.filmLengthText} (without sound) in full-screen mode, and continuously report how
      you feel by moving your mouse.</li>
      <li>Answer some short questions before and after the film, including a short written description
      (at least 100 words) of what you saw and how it made you feel.</li>
    </ul>
    <p>The whole study takes ${s.duration}. You need a desktop or laptop computer with a physical mouse or trackpad
    (not a touchscreen, pen/drawing tablet, or remote-desktop/virtual-machine session).
    Please take part in a quiet room where you can watch the video carefully, without distractions or interruptions.
    You will be paid ${s.payment} through Prolific on completion.</p>

    <h3>Are there any risks?</h3>
    <p><b>Content note:</b> the film is first-person footage of people climbing up and around a very tall
    skyscraper. It contains no violent, sexual or graphic content: nobody is hurt and the climb ends safely.
    Some people find heights footage tense or uncomfortable, and it may be distressing if you have a strong
    fear of heights. If you think you would find this distressing, please do not take part.
    There are no other known risks beyond those of normal computer use.</p>

    <div class="ai-notice">
      <h3>Please do not use AI or automated tools</h3>
      <p>Please do <b>not</b> use AI tools (such as ChatGPT or similar assistants) or any automated software (bots,
      scripts, auto-clickers or browser agents) to complete the task or to answer any of the questions. We are
      interested in <b>your own</b> experience and words. Copying and pasting is disabled, and we record your mouse
      movements, when the study window loses focus, and attempts to copy or paste. If we find clear evidence that AI
      or automated tools were used, your answers will not be used and your submission may be rejected.</p>
    </div>

    <h3>Do I have to take part?</h3>
    <p>No. Taking part is voluntary. You can stop at any time without giving a reason by closing this window
    and returning the study on Prolific. Following Prolific's rules, payment is made for completed
    sessions.</p>

    <h3>What data are collected and how are they used?</h3>
    <p>We collect your Prolific ID, your ratings and answers, and technical information needed to check data
    quality (browser type, screen size, timing of the film and of your responses, your mouse movements during the
    rating task, whether you left full-screen mode or switched to another window, attempts to copy or paste, and
    typing statistics such as the number of keystrokes in your written answer). We do <b>not</b> ask for your name or contact details, and we do not record any video or
    audio of you. We also receive basic demographic information from your Prolific profile (age, sex, first language,
    country of residence, nationality, country of birth, and student and employment status), which we use to describe
    the group of people who took part.</p>
    <p>Your Prolific ID is used only to manage payment and to link your data if you contact us; it is replaced by a
    random code before analysis and is never published. Data are stored on secure servers in the European Union.
    The anonymised data (without Prolific IDs) may be shared in open research repositories and reported in
    scientific publications, in a form that cannot identify you. Data are kept for at least five years after
    the last publication, in line with Aarhus University's research integrity rules.</p>

    <h3>Your data protection rights</h3>
    <p>The data controller is ${s.dataController}. Data are processed for scientific research in the public
    interest (EU General Data Protection Regulation, Article 6(1)(e)). You have the right to request access to,
    correction of, or deletion of your data. To do this, contact us with your Prolific ID. Once data have been
    anonymised we can no longer identify them, so deletion is only possible before that point.
    You can contact Aarhus University's data protection officer at <a href="mailto:${s.dpoEmail}">${s.dpoEmail}</a>,
    and you have the right to complain to the Danish Data Protection Agency (Datatilsynet,
    <a href="https://www.datatilsynet.dk" target="_blank" rel="noopener">www.datatilsynet.dk</a>).</p>

    <h3>Questions?</h3>
    <p>Contact ${s.piName} at <a href="mailto:${s.contactEmail}">${s.contactEmail}</a>,
    or message us through Prolific.</p>`;
  },

  /** Each statement must be ticked to consent. */
  consentStatements: [
    "I have read and understood the information about this study.",
    "I understand that taking part is voluntary and that I can stop at any time without giving a reason.",
    "I understand that the film shows people climbing at great heights, and I do not expect this to be seriously distressing for me.",
    "I understand how my data will be collected, stored and shared, as described above.",
    "I will not use AI tools or automated software to complete the task or answer the questions, and I understand that if clear evidence of their use is found, my answers will not be used and my submission may be rejected.",
    "I am 18 years of age or older.",
    "I agree to take part in this study.",
  ],

  consentButton: "I consent, begin the study",
  declineButton: "I do not wish to take part",

  noConsent: `<div class="text-page"><h2>Thank you</h2>
    <p>You chose not to take part. No data will be used. You will now be returned to Prolific;
    please return the study there.</p></div>`,

  deviceExclusionMobile:
    "<p>This study needs a desktop or laptop computer. Please return the study on Prolific. Thank you for your interest.</p>",
  deviceExclusionSize:
    "<p>Your browser window is too small for this study. Please return the study on Prolific. Thank you for your interest.</p>",

  /** Shown after the post-film questions, before redirecting to Prolific. */
  debrief: (dim) => `<div class="text-page"><h2>Thank you for taking part!</h2>
    <p>You rated <b>${dim.label}</b> continuously while watching the film. In a related study, other participants
    rated their feelings in a different way. By combining many people's ratings over time we can describe how the
    film is experienced moment by moment, and relate this to brain activity recorded from people who watched the
    same film in an MRI scanner.</p>
    <p>If watching the film left you feeling uncomfortable, this usually passes quickly. If it does not, or if you
    have any questions or concerns about the study, please contact ${STUDY_INFO.piName} at
    <a href="mailto:${STUDY_INFO.contactEmail}">${STUDY_INFO.contactEmail}</a>.</p>
    <p>Please do not share details of the film or the study with other potential participants.</p>
    <p>Press the button to save your answers and return to Prolific.</p></div>`,
  /** 2D mode: introduction to the grid before the placement practice. */
  quadrantIntro: `<div class="text-page"><h2>Practice: where do feelings go?</h2>
    <p>During the film you will use a square to show how you feel:</p>
    <ul>
      <li><b>Left &ndash; right:</b> unpleasant &ndash; pleasant, with neutral in the centre.</li>
      <li><b>Down &ndash; up:</b> low &ndash; high activation. Activation means feeling activated or stirred up,
      regardless of whether the feeling is pleasant or unpleasant.</li>
    </ul>
    <p>The same area of the square can hold quite different feelings. For example, being nervous and being
    angry are both <i>unpleasant with high activation</i> (upper-left), while being sad or bored is
    <i>unpleasant with low activation</i> (lower-left).</p>
    <p>Next you will read six short situations. For each one, move the dot to where that feeling belongs and press
    <b>SPACE</b>. You'll see where most people would put it.</p></div>`,

  /** 2D placement practice. Two items per unpleasant quadrant; upper-left is deliberately not only fear. */
  quadrantScenarios: [
    {
      scenario: "You are waiting for important test results and your heart is pounding.",
      expected: { valence: "neg", arousal: "high" },
      explanation: "Feeling nervous or tense is unpleasant, with high activation.",
    },
    {
      scenario: "Someone pushes in front of you in a long queue and you feel your face getting hot.",
      expected: { valence: "neg", arousal: "high" },
      explanation: "Anger is also unpleasant with high activation &ndash; this area holds many different feelings, not just fear.",
    },
    {
      scenario: "After a long, disappointing day you feel tired and low.",
      expected: { valence: "neg", arousal: "low" },
      explanation: "Feeling sad or drained is unpleasant, with low activation.",
    },
    {
      scenario: "You are stuck at home on a grey afternoon with nothing to do, feeling bored and sluggish.",
      expected: { valence: "neg", arousal: "low" },
      explanation: "Boredom is unpleasant, with low activation.",
    },
    {
      scenario: "Your favourite team scores the winning goal in the last minute.",
      expected: { valence: "pos", arousal: "high" },
      explanation: "Excitement is pleasant, with high activation.",
    },
    {
      scenario: "You are lying in a warm bath after a good day.",
      expected: { valence: "pos", arousal: "low" },
      explanation: "Relaxed contentment is pleasant, with low activation.",
    },
  ],

  /**
   * Attention checks: instructed-response items (Prolific-compliant: explicit instruction on the same
   * page, no memory, no time limit). Prolific allows rejection only if BOTH are failed (study > 5 min).
   */
  attentionCheck1: {
    name: "attention_1",
    prompt: "To show that you are reading carefully, please select <b>Strongly disagree</b> for this statement.",
    labels: ["Strongly disagree", "Disagree", "Agree", "Strongly agree"],
    correctIndex: 0,
  },
  attentionCheck2: {
    name: "attention_2",
    prompt: "This is an attention check. Please select <b>Extremely</b> (the option furthest to the right).",
    labels: ["Not at all", "", "", "", "", "", "Extremely"],
    correctIndex: 6,
  },

  bodySensations: [
    "Sweaty or tingling palms",
    "Tingling in the feet or legs",
    "Racing or pounding heart",
    "Butterflies or a sinking feeling in the stomach",
    "Muscle tension or gripping",
    "Holding my breath or faster breathing",
    "Dizziness or a sense of vertigo",
    "None of these",
  ],

  /** Required, minimum finalTextMinWords words. */
  finalTextPrompt: `<h3>Your experience of the video</h3>
    <p>Please describe what you saw in the video and how it made you feel. You may describe particular moments,
    thoughts, or physical sensations, including if you felt little or no emotional response. Please write at least
    100 words.</p>`,
  /** Optional, no minimum. */
  feedbackPrompt:
    "Do you have any comments or feedback about the study, the rating task, or any technical difficulties you experienced? (Optional)",
  finalTextMinWords: 100,

  /**
   * STICSA state form, somatic subscale (Ree, French, MacLeod & Locke, 2008): all 11 items, original
   * item numbers, wording and order. Wording verified against the published state form reproduced in
   * Roberts (2013, York University dissertation, Appendix B); subscale membership also per
   * Frontiers in Psychology 2021, 12:644889, Table 2. Do not add, drop or reword items.
   */
  sticsa: {
    title: "Current feelings",
    instruction: "Please indicate how you feel right now, at this moment.",
    options: [
      { value: 1, label: "Not at all" },
      { value: 2, label: "A little" },
      { value: 3, label: "Moderately" },
      { value: 4, label: "Very much so" },
    ],
    items: [
      [1, "My heart beats fast."],
      [2, "My muscles are tense."],
      [6, "I feel dizzy."],
      [7, "My muscles feel weak."],
      [8, "I feel trembly and shaky."],
      [12, "My face feels hot."],
      [14, "My arms and legs feel stiff."],
      [15, "My throat feels dry."],
      [18, "My breathing is fast and shallow."],
      [20, "I have butterflies in the stomach."],
      [21, "My palms feel clammy."],
    ],
  },

  /** Shown when the film cannot be downloaded in time (study ends, participant asked to return). */
  slowDownload: `<div class="text-page"><h2>Sorry &ndash; the film could not be downloaded</h2>
    <p>Unfortunately your internet connection could not download the film quickly enough, so the study cannot
    continue. This is not your fault.</p>
    <p>You will now be sent back to Prolific. <b>Please return the study</b> there &ndash; returning does not count
    against you. Thank you for your time.</p></div>`,

  // Prolific listing description lives in prolific/study_template.json
};
