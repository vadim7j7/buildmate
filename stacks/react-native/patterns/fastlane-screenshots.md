# Store Screenshots & Metadata: Maestro + Fastlane

Localized App Store / Google Play **screenshots and listing metadata** are produced
by a Maestro → Fastlane pipeline. EAS owns the binary; Fastlane uploads **metadata +
framed screenshots only** (no IPA/AAB, no auto-submit).

## Scaffolded files

- `fastlane/Fastfile` — lanes for both platforms: `caption_screenshots`,
  `stage_screenshots`, `upload_metadata` (iOS via `deliver`, Android via `supply`).
- `fastlane/Appfile` — bundle id / package name / team ids (fill these in).
- `fastlane/capture-screenshots.sh` / `capture-screenshots-ios.sh` — Maestro loops
  over **every locale × device**; the locale list is baked in to match i18n.
- `fastlane/screenshots/render_captions.sh` — ImageMagick framing (brand gradient +
  localized caption).
- `fastlane/flows/screenshots.yaml` — the Maestro flow to capture (edit to your app).
- `fastlane/.creds/` — gitignored store credentials (`asc_api_key.json`,
  `google-play-service-account.json`).

## Pipeline (per platform)

```
make screenshots-android   # capture raw PNGs (Maestro, all locales × devices)
make frame-android         # render_captions.sh → *_framed.png
make stage-android         # copy framed shots into metadata dirs
make upload-android-dry    # validate_only — no live changes
make upload-android        # push metadata + screenshots to the store
```

(iOS: same targets with `-ios`.)

## Rules

- Keep the capture locale set equal to the i18n locale set — they're driven by the
  same configured list. Adding a language means adding its screenshots too.
- Credentials live only in `fastlane/.creds/` and must stay gitignored.
- `upload_metadata` never uploads a binary and never submits for review — that's a
  deliberate, separate step.
- Always run the `*-dry` (validate/verify) target before a live upload.
