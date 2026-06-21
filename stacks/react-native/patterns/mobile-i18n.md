# Mobile Internationalization: i18next + expo-localization

Every user-facing string is localized. The supported locale set is **fixed at
bootstrap and identical to the landing site** — do not add or drop locales ad hoc;
change the `languages` option / profile instead.

## Scaffolded files

- `src/i18n/index.ts` — i18next init, `SUPPORTED_LOCALES`, `DEFAULT_LOCALE`, and
  device-locale resolution via `expo-localization`. The locale list is already
  baked in to match the project's configured set.
- `src/i18n/locales/en.json` — the **source catalog**. Translate from this.

## Adding a language

1. Copy `locales/en.json` → `locales/<code>.json` and translate the values
   (keep the key structure identical).
2. Register it in `src/i18n/index.ts` `resources` (uncomment / add the `require`).
3. Never leave a key untranslated as English silently — fall back is automatic, but
   track coverage.

## Usage

```tsx
import { useTranslation } from "react-i18next";

const { t } = useTranslation();
return <Text>{t("common.continue")}</Text>;
```

## Rules

- No hardcoded display strings in components — every visible string goes through `t()`.
- Use ICU-style interpolation (`t("greeting", { name })`) rather than string concat.
- Keep catalog keys namespaced (`common.*`, `<screen>.*`) and in sync across locales.
- The store-screenshot pipeline captures one set per locale (see fastlane-screenshots),
  so the same locale list drives translations **and** screenshots.
