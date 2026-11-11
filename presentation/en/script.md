# 5-Minute Talk Script (English, for `presentation/en/main.tex`, 11 pages)

> 11 pages including title and outline; target **4 min 45 s**. One main line per page,
> read it as written if needed.

| Time | Page | Title | What to say |
|---|---|---|---|
| 0:00–0:15 | 1 | Title | "Automatic generation of CODESYS Structured Text, focused on comparing our own harness against the Codex CLI baseline in four settings." |
| — | 2 | Outline | Don't stop here; as you turn the page say half a sentence: "Four parts: problem, data, framework, results." |
| 0:15–0:45 | 3 | Problem Overview | "The hard part isn't making the code look plausible: a state machine that is off by one cycle, or a missed priority, still reads fine. So the verdict has to come from a real CODESYS compile and simulation, and every failure has to turn into structured feedback." |
| 0:45–1:10 | 4 | Dataset | "30 tasks, 75 LTL specs, 54 case groups over 199 scan steps, and every step states what it checks. First we pin down that the tasks are solvable and the cases are right: all 30 reference implementations compile and pass their own cases." |
| 1:10–1:45 | 5 | Architecture | "The loop is this figure: generate → zero-cost interface check → compile (about 13 s) → simulate (about 24 s). Any stage that fails becomes structured feedback: an error code with line and column, or the failing case, step, expected value and measured value." |
| 1:45–2:05 | 6 | Experimental Setup | "A 2×2. Codex is wrapped as the same chat interface as our harness: identical prompt, feedback text, round limit, compile and test pipeline. The only difference is how generation is organised, so differences attribute to the framework." |
| 2:05–2:35 | 7 | Overall Results | "On DeepSeek both frameworks are 83.3%, a tie; our first-round compile is 3 points lower but feedback closes it. On Qwen there is still a gap: 66.7% against 46.7%." |
| 2:35–3:00 | 8 | Cost | "At the same pass rate, our input tokens are 13% of Codex's and wall time about half. Output tokens are comparable, so both frameworks think a similar amount — what differs is how much they read. Codex's agent loop keeps re-accumulating context. On Qwen the wall time is actually similar (94%), yet we pass 20 points more." |
| 3:00–3:30 | 9 | Why 1: compile layer | "The gap is first about compiling at all: on DeepSeek both frameworks have zero compile failures, so all losses are behavioural; Codex+Qwen still has 5 tasks that never compile. Among tasks that do compile, behavioural pass rates are 83.3 / 83.3 / 71.4 / 56.0 — on Qwen the gap narrows from 20 points to 15, and the rest comes from tasks that never compiled." |
| 3:30–4:05 | 10 | Why 2: where it comes from | "Three checkable pieces of evidence. First, the share that reaches the compiler in round one: 30/30 for us, 21/30 for Codex — 9 submissions used REAL or BOOL as a DUT name or had no POU block at all, so they never reached the compiler. Second, once inside compilation, error entries per round are 1.17 against 2.66, and the samples are ST written in C style: `!` for negation, `if` with parentheses. Third, on the 13 tasks both frameworks pass, ours averages 1.38 rounds and Codex 2.00, with first-round compiles of 23/30 against 9/30. So it is not that Codex cannot do certain tasks — with the same capability it needs more rounds to converge, and the limit is 5. To be honest: the Fisher exact test on 20/30 versus 14/30 gives p = 0.19, not significant, so the conclusion rests on these three mechanistic results, not on the single pass rate." |
| 4:05–4:45 | 11 | Conclusion | "One sentence: turning 'does it compile, does it run correctly' into structured feedback lifts weak models; but no framework is better for every model. The limitations are on the slide: specs not connected to PLCVerif, gaps in case coverage, one sample per task." |

## Likely questions

- **Why isn't 83.3% higher?** Of the 5 failures, `public_hard_003` and `self_easy_003`
  fail in all 4 settings, and `public_easy_005`, `public_hard_004`,
  `public_medium_003` fail in 3 settings, which points at the strength of the cases and
  specs rather than model capability; the rest are genuine behavioural errors in state
  machines and timing/edge tasks.
- **Is Codex misconfigured on Qwen?** The feedback text, round limit, compile and test
  pipeline are identical to our harness; Codex only adds its own agent loop, and with
  DeepSeek it reaches 83.3%. The result is an interaction effect, not a configuration
  difference.
- **Does our harness only save tokens?** No. On DeepSeek quality ties while cost drops by
  an order of magnitude; on Qwen quality is also 20 points higher.
- **Are the pass rates optimistic?** They are rates "under the current test cases"; report
  §5.7 lists the gaps (12 steps with no assertion, 34 BOOL inputs never set TRUE), so
  tighter cases could lower them.
- **How are tokens counted?** Accumulated over 30 tasks per setting (`tokens_in` /
  `tokens_out` in `experiments/results.csv`); Codex's tool-call overhead is included.
- **Is the difference statistically significant?** No: one sample per task, Fisher exact
  p = 0.19. The claim rests on the mechanistic evidence in §5.6.2.

## Before presenting

- [ ] `latexmk -g -xelatex main.tex`; `main.pdf` should be 11 pages with 0 overfull boxes.
- [ ] The style is shared (`\usepackage{../zh/zju_beamer}`), so a style edit in
      `../zh/` carries over. The `figures/` here are copies — `\pgfdeclareimage`
      ignores `\graphicspath`, so sync them by hand if you change the artwork.
- [ ] Page 7 highlights the Codex+Qwen row in red — point at it, don't read the table.
