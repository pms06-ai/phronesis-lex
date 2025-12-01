# Documentation Index

Central home for every Markdown artifact in this workspace so the investigation
does not depend on scattered files or forgotten repos.

## Structure
- `docs/core/` – living specs and operational guides needed day-to-day.
- `docs/archive/` – historical reports, attribution logs, and AI research notes
  preserved for reference.
- `markdown_inventory.csv` – auto-generated manifest listing every `.md` file
  (path, size, timestamp, SHA-256) so duplicates can be spotted quickly or
  imported into spreadsheets.

## Core References
- `docs/core/FCIP_FRONTEND_SPEC.md` – UI contract for FCIP visualisations
  (bias report, Toulmin arguments, entity panel, deadlines, legal rules).
- `docs/core/NEW_FILES_ANALYSIS.md` – running changelog describing fresh
  evidence drops and ingestion status.
- `docs/core/PARTIES_AND_ROLES.md` – taxonomy of parties/capacities used across
  entity resolution, deadlines, and reporting.
- `docs/core/DEPLOYMENT.md` – local + container startup notes; canonical copy
  lives here, with older duplicates in legacy clones.

## Archived Reports
- `docs/archive/CASE_QA_REPORT.md` – QA outcomes for prior case ingest cycles.
- `docs/archive/DEAD_CODE_REPORT.md` – inventory of unused modules/components.
- `docs/archive/DOCUMENT_ATTRIBUTION_LOG.md` – audit trail of document sources.
- `docs/archive/EMAIL_COMMUNICATIONS_LOG.md` – correspondence digests pulled
  from email exports.
- `docs/archive/POLICE_WITNESS_ANALYSIS.md` – legacy analysis notes.
- `docs/archive/POLICE_WITNESS_STATEMENTS.md` – extracted witness statements.

## Duplicates and External Copies
- `docs/core/DEPLOYMENT.md` duplicates `Phronesis/fresh-clone/DEPLOYMENT.md`.
  Keep the new `docs/core` version as canonical; treat the `Phronesis/` copy as
  archive-only.
- Library/vendor docs originating from the Python virtual env or npm packages
  are intentionally left out of this index. If additional exclusions are
  needed, update the inventory script to extend the filter list.

## Next Steps
1. Import the 16 GitHub repos (or their key branches) into `archive/` via
   `git subtree` so every iteration of this project is preserved beside the
   working tree.
2. Wire intake automations so any PDF, AI memo, or exported note dropped into
   `data/uploads/` lands in the database and gets surfaced in the control
   center UI.
3. Keep regenerating `markdown_inventory.csv` after large refactors with:
   ```powershell
   pwsh -NoLogo -NoProfile -Command "
     $files = Get-ChildItem -Path . -Filter *.md -Recurse -File |
       Where-Object {
         $_.FullName -notlike '*\node_modules\*' -and
         $_.FullName -notlike '*\.git\*' -and
         $_.FullName -notlike '*\venv\*'
       };
     $files | ForEach-Object {
       $hash = (Get-FileHash -Algorithm SHA256 $_.FullName).Hash;
       [PSCustomObject]@{
         Path     = $_.FullName.Substring((Get-Location).Path.Length + 1);
         SizeKB   = [math]::Round($_.Length / 1KB, 1);
         LastWrite= $_.LastWriteTime;
         Hash     = $hash
       }
     } | Sort-Object Path | Export-Csv -NoTypeInformation markdown_inventory.csv
   "
   ```


