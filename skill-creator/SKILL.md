---
name: skill-creator
description: Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy. Use this even if the user just says "turn this workflow into a reusable skill" or "make this repeatable."
---

# Skill Creator

A skill for creating new skills and iteratively improving them. It is written for any capable AI agent, regardless of the platform or tooling it runs on. Where a step depends on a capability your environment may lack (parallel sub-agents, a browser, a command-line agent runner), a fallback is given.

## The process at a glance

1. Decide what the skill should do and roughly how.
2. Write a draft of the skill.
3. Create a few realistic test prompts and run an agent that has access to the skill on them.
4. Evaluate the results with the user, qualitatively and (where sensible) quantitatively.
   - While runs are in progress, draft quantitative checks if none exist, and explain them to the user.
   - Show the user the outputs and any metrics in whatever review format your environment supports.
5. Rewrite the skill based on the user's feedback and any glaring flaws the metrics reveal.
6. Repeat until satisfied, then expand the test set and try again at larger scale.
7. Optionally, optimize the skill's description for better triggering.
8. Package the final skill and hand it to the user.

Your job is to work out where the user is in this process and help them move forward. If they say "I want a skill for X," help narrow it down, draft it, write test cases, decide how to evaluate, run the prompts, and iterate. If they already have a draft, go straight to the evaluate-and-iterate part. If they say "I don't need evals, just work with me on it," do that instead. Stay flexible.

## Communicating with the user

Users range from seasoned developers to people who have only just started using AI agents for automation. Read context cues and match your vocabulary:

- "evaluation" and "benchmark" are borderline but generally fine.
- Terms like "JSON," "assertion," or "subagent" need clear signals that the user knows them before you use them without explanation.

When in doubt, add a short definition in passing.

---

## Creating a skill

### Capture intent

Start by understanding what the user wants. The conversation may already contain a workflow they want to capture ("turn this into a skill"). If so, extract answers from the history first: tools used, sequence of steps, corrections the user made, input/output formats. Let the user fill gaps and confirm before moving on.

Clarify:

1. What should this skill enable the agent to do?
2. When should it trigger (which user phrases or contexts)?
3. What is the expected output format?
4. Should we set up test cases? Skills with objectively checkable outputs (file transforms, data extraction, code generation, fixed workflows) benefit from them. Skills with subjective outputs (writing style, art) usually don't. Suggest a sensible default, but let the user decide.

### Interview and research

Ask about edge cases, input/output formats, example files, success criteria, and dependencies. Don't write test prompts until this is settled. If you have tools for research (documentation search, finding similar skills, best-practice lookups), use them, in parallel if possible, so you arrive with context and the user carries less of the burden.

### Write the SKILL.md

Fill in these components:

- **name**: the skill identifier.
- **description**: what the skill does and when to use it. This is the primary triggering mechanism, so put all "when to use" information here, not in the body. Agents tend to *undertrigger* skills, so make descriptions a little pushy. Instead of "How to build a simple dashboard for internal data," write "How to build a simple dashboard for internal data. Use this whenever the user mentions dashboards, data visualization, internal metrics, or wants to display any kind of company data, even if they don't explicitly ask for a 'dashboard.'"
- **compatibility** (optional, rarely needed): required tools or dependencies.
- **The body**: the instructions themselves.

### Skill writing guide

#### Anatomy of a skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description required)
│   └── Markdown instructions
└── Bundled resources (optional)
    ├── scripts/    - Executable code for deterministic or repetitive tasks
    ├── references/ - Docs loaded into context as needed
    └── assets/     - Files used in output (templates, icons, fonts)
```

#### Progressive disclosure

Skills load in three levels:

1. **Metadata** (name + description): always in context (~100 words).
2. **SKILL.md body**: in context whenever the skill triggers (under ~500 lines is ideal).
3. **Bundled resources**: loaded as needed; scripts can run without being read into context.

These sizes are approximate; go longer if needed.

Key patterns:

- Keep SKILL.md under ~500 lines. If you approach the limit, add a layer of hierarchy with clear pointers to where the agent should look next.
- Reference bundled files clearly from SKILL.md, saying when to read them.
- Give large reference files (>300 lines) a table of contents.

When a skill supports multiple domains or frameworks, organize by variant so the agent reads only what it needs:

```
cloud-deploy/
├── SKILL.md (workflow + selection)
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```

#### Principle of lack of surprise

Skills must not contain malware, exploit code, or anything that could compromise system security. A skill's contents should not surprise the user given its description. Don't help create misleading skills or skills meant to enable unauthorized access, data exfiltration, or other malicious activity. Role-play skills ("act as an XYZ") are fine.

#### Writing patterns

Prefer the imperative form.

**Defining output formats:**

```markdown
## Report structure
Use this exact template:
# [Title]
## Executive summary
## Key findings
## Recommendations
```

**Examples:**

```markdown
## Commit message format
**Example 1:**
Input: Added user authentication with JWT tokens
Output: feat(auth): implement JWT-based authentication
```

### Writing style

Explain *why* things matter instead of issuing rigid, all-caps commands. Modern models have good theory of mind; given the reasoning, they handle cases the author never anticipated. Keep the skill general rather than narrowly fitted to a few examples. Write a draft, then reread it with fresh eyes and improve it.

### Test cases

After drafting, come up with 2-3 realistic test prompts, the kind a real user would actually type. Share them with the user ("Here are a few test cases I'd like to try. Do these look right, or do you want to add more?"), then run them.

Save them to `evals/evals.json`. Don't write assertions yet, just prompts; you'll draft assertions while runs are in progress.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's task prompt",
      "expected_output": "Description of expected result",
      "files": []
    }
  ]
}
```

See `references/schemas.md` for the full schema, including the `assertions` field added later.

---

## Running and evaluating test cases

Treat this section as one continuous sequence; don't stop partway through.

Put results in `<skill-name>-workspace/`, a sibling of the skill directory. Organize by iteration (`iteration-1/`, `iteration-2/`, ...) and, within each, by test case (`eval-0/`, `eval-1/`, ...). Create directories as you go.

### Step 1: Run every test case, with the skill and a baseline

For each test case, do two runs: one with the skill, one baseline. If your environment supports parallel sub-agents (independent agent instances), launch all runs at once so they finish at about the same time. If not, run them sequentially yourself (see "Adapting to your environment" below).

**With-skill run** — give the executing agent:

```
Execute this task:
- Skill path: <path-to-skill>
- Task: <eval prompt>
- Input files: <eval files if any, or "none">
- Save outputs to: <workspace>/iteration-<N>/eval-<ID>/with_skill/outputs/
- Outputs to save: <what the user cares about, e.g. "the .docx file", "the final CSV">
```

**Baseline run** — same prompt; the baseline depends on context:

- *Creating a new skill*: no skill at all. Save to `without_skill/outputs/`.
- *Improving an existing skill*: the old version. Before editing, snapshot it (`cp -r <skill-path> <workspace>/skill-snapshot/`) and point the baseline run at the snapshot. Save to `old_skill/outputs/`.

Write an `eval_metadata.json` for each test case (assertions may be empty for now). Give each eval a descriptive name reflecting what it tests, and use that name for the directory too. If an iteration uses new or modified prompts, create these files for each new eval directory; don't assume they carry over.

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name-here",
  "prompt": "The user's task prompt",
  "assertions": []
}
```

### Step 2: While runs are in progress, draft assertions

Use the waiting time. Draft quantitative assertions for each test case and explain them to the user. If assertions already exist in `evals/evals.json`, review them and explain what they check.

Good assertions are objectively verifiable and have descriptive names that read clearly in a results viewer. Subjective skills (writing style, design quality) are better judged qualitatively; don't force assertions onto things that need human judgment.

Update `eval_metadata.json` and `evals/evals.json` once assertions are drafted. Tell the user what they'll see when reviewing: both the qualitative outputs and the quantitative benchmark.

### Step 3: Capture timing data as runs complete

If your environment reports token counts and duration for each completed run, record them immediately in `timing.json` in that run's directory. This data is often only available at completion time and is not persisted elsewhere, so don't batch it up for later.

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

If your environment doesn't expose this, skip it or record approximate wall-clock time.

### Step 4: Grade, aggregate, and present

Once all runs are done:

1. **Grade each run.** Evaluate each assertion against the outputs, using a separate grader agent if available (reading `agents/grader.md`) or inline otherwise. Save results to `grading.json` in each run directory. The `expectations` array must use the fields `text`, `passed`, and `evidence` (not `name`/`met`/`details` or other variants); the viewer depends on these exact names. For assertions that can be checked programmatically, write and run a script rather than eyeballing; scripts are faster, more reliable, and reusable across iterations.

2. **Aggregate into a benchmark.** If the bundled scripts are available, run from the skill-creator directory:

   ```bash
   python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
   ```

   This produces `benchmark.json` and `benchmark.md` with pass rate, time, and tokens per configuration, with mean ± stddev and the delta. If generating `benchmark.json` by hand, see `references/schemas.md` for the schema. List each with-skill result before its baseline counterpart.

3. **Do an analyst pass.** Read the benchmark and surface patterns the aggregates hide (see the "Analyzing Benchmark Results" section of `agents/analyzer.md`): assertions that always pass regardless of the skill (non-discriminating), high-variance evals (possibly flaky), and time/token tradeoffs.

4. **Present results for review.** If a browser or display is available, launch the bundled viewer:

   ```bash
   nohup python <skill-creator-path>/eval-viewer/generate_review.py \
     <workspace>/iteration-N \
     --skill-name "my-skill" \
     --benchmark <workspace>/iteration-N/benchmark.json \
     > /dev/null 2>&1 &
   VIEWER_PID=$!
   ```

   For iteration 2+, also pass `--previous-workspace <workspace>/iteration-<N-1>`.

   If no browser or display is available, add `--static <output_path>` to write a standalone HTML file, and give the user the path or link to open. Feedback will be downloaded as `feedback.json` when they click "Submit All Reviews"; copy it into the workspace for the next iteration. If the viewer can't be used at all, show each prompt and output directly in the conversation and collect feedback inline.

   Use `generate_review.py` rather than writing custom HTML. And get the outputs in front of the human *before* you start analyzing and revising on your own; their eyes on real examples is the most valuable signal you have.

5. **Tell the user** what to expect, for example: "I've opened the results. There are two tabs: 'Outputs' lets you click through each test case and leave feedback, and 'Benchmark' shows the quantitative comparison. Let me know when you're done."

### What the viewer shows

The "Outputs" tab shows one test case at a time:

- **Prompt**: the task given.
- **Output**: the files the skill produced, rendered inline where possible.
- **Previous Output** (iteration 2+): collapsed view of last iteration's output.
- **Formal Grades** (if grading ran): collapsed assertion pass/fail.
- **Feedback**: a textbox that auto-saves.
- **Previous Feedback** (iteration 2+): the user's earlier comments.

The "Benchmark" tab shows pass rates, timing, and token usage per configuration, with per-eval breakdowns and analyst notes. Navigation is via prev/next buttons or arrow keys; "Submit All Reviews" saves everything to `feedback.json`.

### Step 5: Read the feedback

When the user is done, read `feedback.json`:

```json
{
  "reviews": [
    {"run_id": "eval-0-with_skill", "feedback": "the chart is missing axis labels", "timestamp": "..."},
    {"run_id": "eval-1-with_skill", "feedback": "", "timestamp": "..."},
    {"run_id": "eval-2-with_skill", "feedback": "perfect, love this", "timestamp": "..."}
  ],
  "status": "complete"
}
```

Empty feedback means the user thought it was fine. Focus improvements on cases with specific complaints. When finished, stop the viewer server:

```bash
kill $VIEWER_PID 2>/dev/null
```

---

## Improving the skill

This is the heart of the loop: you've run the tests, the user has reviewed them, and now you make the skill better.

### How to think about improvements

1. **Generalize from the feedback.** The skill will be used many times across many different prompts, but you and the user are iterating on only a few examples because it's fast. If the skill only works for those examples, it's useless. Avoid fiddly, overfit patches and oppressive rules. If a stubborn issue persists, try a different metaphor or recommend a different working pattern; it's cheap to try.

2. **Keep the prompt lean.** Remove what isn't pulling its weight. Read the run transcripts, not just final outputs. If the skill is making the agent waste time on unproductive steps, remove the parts causing it and see what happens.

3. **Explain the why.** Even when feedback is terse or frustrated, work out what the user actually wants and why, then transmit that understanding in the instructions. If you catch yourself writing ALWAYS or NEVER in capitals, or building rigid structures, treat it as a yellow flag and reframe with reasoning instead.

4. **Look for repeated work across test cases.** If every run independently wrote a similar helper script (e.g. `create_docx.py`, `build_chart.py`), bundle it in `scripts/` once and tell the skill to use it. That saves every future invocation from reinventing it.

Take your time. Write a draft revision, then look at it anew and improve it. Try to get into the user's head and understand what they need.

### The iteration loop

1. Apply your improvements.
2. Rerun all test cases into a new `iteration-<N+1>/` directory, including baselines. For a new skill, the baseline stays `without_skill`. For an existing skill, use judgment: the original version the user came in with, or the previous iteration.
3. Present results for review, pointing the viewer at the previous iteration (`--previous-workspace`) when available.
4. Wait for the user to finish reviewing.
5. Read the new feedback, improve again, repeat.

Stop when the user is happy, all feedback is empty, or you're no longer making meaningful progress.

---

## Advanced: blind comparison

For a more rigorous comparison between two versions of a skill (e.g. "is the new version actually better?"), use blind comparison: give two outputs to an independent agent without saying which is which, let it judge quality, then analyze why the winner won. See `agents/comparator.md` and `agents/analyzer.md`. This is optional and requires the ability to run independent agents; the human review loop is usually enough.

---

## Description optimization

The `description` field in the frontmatter is the main mechanism that decides whether an agent invokes a skill. After creating or improving a skill, offer to optimize it.

### Step 1: Generate trigger eval queries

Create about 20 queries, a mix of should-trigger and should-not-trigger, saved as JSON:

```json
[
  {"query": "the user prompt", "should_trigger": true},
  {"query": "another prompt", "should_trigger": false}
]
```

Queries must be realistic: concrete, specific, with detail such as file paths, job context, column names, company names, or URLs, plus a bit of backstory. Mix lengths, and include casual speech, abbreviations, and typos. Favor edge cases over clear-cut ones.

Bad: `"Format this data"`, `"Extract text from PDF"`, `"Create a chart"`

Good: `"ok so my boss just sent me this xlsx file (its in my downloads, called something like 'Q4 sales final FINAL v2.xlsx') and she wants me to add a column that shows the profit margin as a percentage. The revenue is in column C and costs are in column D i think"`

**Should-trigger (8-10):** cover different phrasings of the same intent, formal and casual. Include cases where the user doesn't name the skill or file type but clearly needs it, uncommon use cases, and cases where this skill competes with another but should win.

**Should-not-trigger (8-10):** the most valuable are near-misses that share keywords or concepts with the skill but need something different: adjacent domains, ambiguous phrasing where naive keyword matching would wrongly trigger, and cases where another tool is more appropriate. Don't use obviously irrelevant negatives like "write a fibonacci function" for a PDF skill; they test nothing.

### Step 2: Review with the user

Bad eval queries lead to bad descriptions, so have the user sign off. If the bundled template is available:

1. Read `assets/eval_review.html`.
2. Replace the placeholders: `__EVAL_DATA_PLACEHOLDER__` with the JSON array (no surrounding quotes, since it's a JS variable assignment), `__SKILL_NAME_PLACEHOLDER__` with the skill name, `__SKILL_DESCRIPTION_PLACEHOLDER__` with the current description.
3. Write it to a temp file (e.g. `/tmp/eval_review_<skill-name>.html`) and open it for the user.
4. The user edits queries, toggles should-trigger, adds or removes entries, and clicks "Export Eval Set".
5. The file downloads to `~/Downloads/eval_set.json`; check for the most recent copy in case of duplicates like `eval_set (1).json`.

If you can't open a browser, present the queries in the conversation and ask the user to confirm or edit them.

### Step 3: Run the optimization loop

This requires an environment where you can invoke an agent runner from the command line to test triggering. If you don't have one, skip automated optimization and instead improve the description by hand, using the should-trigger and should-not-trigger queries as a mental checklist.

Tell the user: "This will take some time. I'll run the optimization loop in the background and check on it periodically." Save the eval set to the workspace, then run:

```bash
python -m scripts.run_loop \
  --eval-set <path-to-trigger-eval.json> \
  --skill-path <path-to-skill> \
  --model <model-id-powering-this-session> \
  --max-iterations 5 \
  --verbose
```

Use the ID of the model powering the current session so triggering tests match what the user actually experiences. Periodically tail the output and update the user on the iteration and scores.

The loop splits the eval set 60% train / 40% held-out test, evaluates the current description (running each query 3 times for a reliable trigger rate), asks a model to propose improvements based on failures, re-evaluates on both sets, and iterates up to 5 times. It returns JSON with `best_description`, chosen by *test* score rather than train score to avoid overfitting.

### How skill triggering works

Skills appear in the agent's available-skills list as name + description, and the agent decides whether to consult one from that description alone. Agents typically consult skills only for tasks they can't easily handle directly; a simple one-step request like "read this PDF" may not trigger a skill even with a perfect description. Complex, multi-step, or specialized queries trigger reliably when the description matches. So make eval queries substantive enough that a skill would actually help.

### Step 4: Apply the result

Take `best_description` and update the SKILL.md frontmatter. Show the user before and after, and report the scores.

---

## Packaging and delivery

Package the finished skill so the user can install it:

```bash
python -m scripts.package_skill <path/to/skill-folder>
```

This produces a `.skill` file (a packaged skill archive). Give the user its path, or share it using whatever file-delivery mechanism your environment provides. If you have no way to hand files to the user, tell them where the file is on disk.

---

## Adapting to your environment

The core workflow (draft, test, review, improve, repeat) is the same everywhere, but available capabilities change the mechanics.

**With parallel sub-agents and a shell:** use the full workflow above, including with-skill and baseline runs in parallel, timing capture, grading agents, and blind comparison. If you hit timeouts, run test prompts in series.

**Without sub-agents:** for each test case, read the skill's SKILL.md and follow it yourself to complete the test prompt, one case at a time. This is less rigorous because you wrote the skill and have full context, but it's a useful sanity check, and the human review compensates. Skip baseline runs and just complete the task with the skill. Skip quantitative benchmarking (it depends on baselines) and focus on qualitative feedback. Skip blind comparison.

**Without a browser or display:** use `--static <output_path>` for the viewer, or present results inline in the conversation. For file outputs (documents, spreadsheets), save them somewhere the user can access and tell them where. Ask for feedback inline: "How does this look? Anything you'd change?"

**Without a command-line agent runner:** skip automated description optimization and refine the description manually.

**Updating an existing skill:** the user may want to improve a skill, not create a new one.

- **Preserve the original name.** Keep the directory name and the `name` frontmatter field unchanged. If the installed skill is `research-helper`, output `research-helper.skill`, not `research-helper-v2`.
- **Copy to a writable location before editing.** The installed path may be read-only. Copy to `/tmp/skill-name/`, edit there, and package from the copy.
- **If packaging manually, stage in `/tmp/` first**, then copy to the output directory; direct writes may fail on permissions.

---

## Reference files

The `agents/` directory holds instructions for specialized sub-agents. Read the relevant one when you need that role (or when playing it yourself if you have no sub-agents):

- `agents/grader.md` — how to evaluate assertions against outputs
- `agents/comparator.md` — how to do blind A/B comparison between two outputs
- `agents/analyzer.md` — how to analyze why one version beat another

The `references/` directory has additional documentation:

- `references/schemas.md` — JSON structures for `evals.json`, `grading.json`, and so on

---

## The core loop, once more

- Figure out what the skill is about.
- Draft or edit the skill.
- Run an agent with access to the skill on test prompts.
- With the user, evaluate the outputs: build `benchmark.json` and put results in front of them for review, and run quantitative checks where they make sense.
- Repeat until you and the user are satisfied.
- Package the final skill and return it to the user.

If you keep a task list, add these steps so none gets forgotten, especially "create the evals JSON and present results for human review before revising on your own."
