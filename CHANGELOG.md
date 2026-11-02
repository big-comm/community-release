# Changelog

## 2.1.0 — 2026-10-24

- Add a responsive terminal dashboard with the current BigCommunity owl.
- Add optional `--tui` / `-t` mode with scrolling, refresh and community links.
- Draw distribution identity before querying the local package database.
- Read only distribution identity for short queries; accept combined flags such
  as `-rs` and `-as` without importing Rich or Textual.
- Query updates offline and show failures as unavailable. Counts describe the
  existing local database rather than a newly synchronized repository state.
- Keep the source checkout runnable alongside an installed version.
- Add gettext extraction/merge, regression tests, CI and a local package build
  from a checksummed archive of the committed tree.
- Exclude interpreter-specific bytecode caches from the distribution package.

This changes the information tool; the distribution remains 1.7.0 Powerful.
