---
id: TASK-0001
title: Check which data files are actually used
status: Done
assignee:
  - Codex
created_date: '2026-01-17 22:08'
updated_date: '2026-01-17 22:10'
labels: []
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
In public/data we have a lot of data files. I need to check if any of them are not in use by the app code.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Check if each data file is used
- [x] #2 Make a list of any unused file
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1) Inventory public/data files (including subfolders like streaming/).
2) Scan src/ for data fetch/usage patterns to map referenced files.
3) Cross-check inventory vs references; flag files not referenced or only referenced via dynamic patterns.
4) Produce concise list of unused files, noting any ambiguous cases needing runtime confirmation.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Audit results (code references in src/):

Used: band_positions.json, brass_positions.json, piece_metadata.json, brass_piece_metadata.json, piece_streaming_links.json, elite_test_pieces.json, repertoire.json, wind_prizes.json, brass_prizes.json, promotion_rules.json, upcoming_wind_2026.json, upcoming_brass_2026.json.

Unused (no code references found): piece_streaming_links_full.json; streaming/brass/2012.json, 2013.json, 2014.json, 2015.json, 2016.json, 2017.json, 2018.json, 2019.json, 2020.json, 2023.json, 2024.json, 2025.json; streaming/wind/2012.json, 2013.json, 2014.json, 2015.json, 2016.json, 2017.json, 2018.json, 2019.json, 2022.json, 2023.json, 2024.json, 2025.json.

Note: streaming/year files only mentioned in AGENTS.md; no runtime fetch found.
<!-- SECTION:NOTES:END -->
