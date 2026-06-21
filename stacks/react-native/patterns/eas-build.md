# Builds & Releases: EAS + Makefile

Native builds, store submission, and OTA updates go through **EAS** (Expo Application
Services), orchestrated by the project `Makefile`.

## Scaffolded files

- `eas.json` — three build profiles: `development` (dev client), `preview` (internal
  distribution / TestFlight + internal track), `production` (store).
- `Makefile` — build / submit / OTA / screenshot targets (`make help` lists them).

## Common flows

```
make build-dev            # development client
make build-preview-ios    # internal/TestFlight build
make ship-prod-ios        # build + submit production iOS
make ship-prod-android    # build + submit production Android
make update-prod MESSAGE="fix: ..."   # OTA JS-only update
make verify               # lint + typecheck + test (CI gate)
```

## Channels & profiles

- The EAS `channel` per profile (`development`/`preview`/`production`) must match the
  `expo-updates` runtime config so OTA updates land on the right binary.
- `appVersionSource: remote` — EAS owns the build number; `autoIncrement` is on for
  preview/production. Don't hand-bump native versions.

## Rules

- Use `preview` for internal QA, `production` only for store releases.
- OTA (`eas update`) ships **JS/asset** changes only — anything touching native code or
  config plugins needs a new binary build.
- Fill in the real `ascAppId` / Android track in `eas.json` `submit` before shipping.
