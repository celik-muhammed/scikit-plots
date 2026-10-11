---
title: "Native GitLab, Bitbucket and Hugging Face feedback adapters"
status: open
kind: "other"
area: "scikitplot/_externals/_sphinx_ext/_sphinx_feedback/_service"
discovered_during: "round 29: page feedback for any site and any storage, 2026-10-11"
release_note: "required"
towncrier_section: "scikitplot._externals._sphinx_ext._sphinx_feedback"
towncrier_type: "feature"
towncrier_fragment: ""
---

# Native GitLab, Bitbucket and Hugging Face feedback adapters

## Summary

`gitlab`, `bitbucket` and `huggingface` are accepted by the storage-target
schema (`_service/_config.py`, `REVIEW_PROVIDERS`) but refused at start
because `IMPLEMENTED_PROVIDERS` does not list them. Sites that keep their
review repository on those hosts today use the `webhook` provider (their own
pipeline or receiver) or a `custom` adapter.

## Why it matters

A reviewed merge/pull request on the site's own forge is the natural review
path for projects outside GitHub, including self-managed GitLab and Bitbucket
Data Center on intranets.

## Current evidence

- `load_service_config` with a `gitlab` primary raises "configured feedback
  provider adapter(s) are not implemented in this release: gitlab".
- `_service/_github.py` is the only reviewed-provider adapter (714 lines with
  reconciliation after every ambiguous step).

## Root cause / current understanding

Not a defect: the adapters were never written. Each needs the GitHub
adapter's guarantees re-established against another API: deterministic
branch per event, one-file diff verification, reconciliation after a broken
connection at each step, bounded responses, no redirects, review-URL host
pinning.

## Expected behavior

`provider: "gitlab"` (with `api_url` for self-managed instances, default
`https://gitlab.com/api/v4`) and `provider: "bitbucket"` (Cloud
`https://api.bitbucket.org/2.0`, Data Center `api_url`) open one merge/pull
request per event with the same idempotency semantics as `github`.

## Affected paths and ownership

`_service/_config.py` (`IMPLEMENTED_PROVIDERS`, `api_url` key for the new
providers), new `_service/_gitlab.py`, `_service/_bitbucket.py`, `_core.py`
dispatch, the proxy mirror (`sync_page_feedback_runtime.py`).

## Constraints and non-goals

No adapter ships without the GitHub-level replay/broken-pipe tests against a
mock transport. Credentials stay server-side through `token_env`.

## Edge cases to cover

Branch names with the `feedback/<nonce>` namespace on each forge; protected
branches; API pagination of merge-request lookups; self-signed intranet CAs
(operator CA bundle, never disabled verification).

## Proposed direction

Factor the GitHub adapter's provider-neutral steps (event path, content
match, bounded request) into a shared module first, then implement GitLab,
then Bitbucket. Hugging Face last: its dataset commit API has no review step,
so it may belong with the `local`-style providers instead.

## Verification / acceptance criteria

Per adapter: fresh submission, replay, conflict, broken pipe after each step,
redirect refusal, oversized response, foreign review URL, all against
`httpx.MockTransport`.

## Documentation impact

README "Storage providers" table; `_example_conf.py` section 9.

## Release-note promotion

Feature fragment under `scikitplot._externals._sphinx_ext._sphinx_feedback`.
