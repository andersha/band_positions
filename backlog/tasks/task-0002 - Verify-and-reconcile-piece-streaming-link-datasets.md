---
id: TASK-0002
title: Verify and reconcile piece streaming link datasets
status: Done
assignee:
  - Codex
created_date: '2026-01-17 22:15'
updated_date: '2026-01-17 22:17'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Compare the streaming link datasets in public/data to confirm whether the full dataset supersedes the current runtime file, and update the runtime dataset accordingly without losing existing entries.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Compare piece_streaming_links.json against piece_streaming_links_full.json and identify any missing/extra entries.
- [x] #2 If full dataset is a superset, replace or merge so the runtime dataset contains all links without duplicates.
- [x] #3 Document the decision and any data changes in task notes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1) Inspect public/data/piece_streaming_links.json and public/data/piece_streaming_links_full.json to confirm schema/keys.
2) Diff datasets by entry keys to determine superset/divergences.
3) If full is superset, replace runtime file or merge if needed to preserve all links without duplicates.
4) Record findings and any updates in task notes.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Comparison results: piece_streaming_links_full.json is NOT a superset. It has 1295 wind entries and 0 brass; current file had 2004 wind / 1174 brass. Full contains 18 wind entries not in current, while current contains 723 wind entries not in full.

Merge action: updated public/data/piece_streaming_links.json by filling missing fields from full for matching keys (317 fields filled) and appending 18 missing wind entries. No brass changes.

Conflicts: 441 overlapping wind entries had differing non-empty fields; kept existing current values and only filled blanks.
<!-- SECTION:NOTES:END -->
