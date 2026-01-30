---
id: TASK-0003
title: Generate conflict report for streaming link datasets
status: Done
assignee:
  - Codex
created_date: '2026-01-17 22:18'
updated_date: '2026-01-17 23:27'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Produce a reviewable report of entries where piece_streaming_links.json and piece_streaming_links_full.json disagree on non-empty field values.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Identify overlapping entries where both datasets have non-empty values that differ.
- [x] #2 Write the conflict details to a separate file for review, including key fields and both values.
- [x] #3 Document the output file path in task notes.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1) Compare public/data/piece_streaming_links.json and public/data/piece_streaming_links_full.json on shared keys (year/division/band/result_piece).
2) Collect conflicts where both have non-empty values that differ (recording_title, album, spotify, apple_music).
3) Write a JSON report file with key fields and both values, and note the output path in the task.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Generated conflict report with 157 entries: public/data/piece_streaming_links_conflicts.json.
<!-- SECTION:NOTES:END -->
