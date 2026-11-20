# MAME AlphaSmart tests

This repository holds MAME device and emulator validation. Tests of Betawise
features belong in the Betawise repository; do not import them here.

Evaluate Neo screens locally and deterministically, without network/model
inference. Use exact pixel assertions or verified font profiles. Unknown or
incomplete captures and timeouts fail validation. Preserve raw records, hashes,
logs and assertion results. Do not regenerate expectations from failed captures.
Use disposable flash/RAM/configuration and never mutate user saved sessions.
Do not commit ROMs, firmware, executable builds, or private run artifacts.

## Commit messages

* Use a short, imperative subject describing the concrete change, for example
  `Add D11 endpoint reset regression tests` or `Fix shared interrupt level checks`.
* Separate the subject from the body with a blank line. For substantive changes,
  explain what changed and why, the behavior covered, and relevant validation
  results or limits. Keep simple documentation changes concise.
* Describe the final change for a reader without the chat history. Avoid generic
  subjects such as `Update tests` and omit internal task identifiers and agent
  workflow details.
* When AI assistance was used, add a separate final paragraph identifying the
  actual tool, model, and version, for example:
  `AI disclosure: assisted by Codex (GPT-6.1 Sol).`
  Do not infer a model from a tool name or copy an earlier disclosure without
  checking it. Preserve attribution for imported contributions and distinguish
  original assistance from assistance used during porting when applicable.
