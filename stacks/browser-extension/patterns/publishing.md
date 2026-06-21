# Publishing

Ship the same codebase to the Chrome Web Store, Firefox Add-ons (AMO), and the Edge
Add-ons store. WXT produces store-ready zips and can automate submission.

## 1. Build store zips

```bash
npm run zip            # .output/<name>-<version>-chrome.zip
npm run zip:firefox    # Firefox zip + a *-sources.zip (AMO requires source for review)
wxt zip -b edge        # Edge zip
```

`wxt zip` runs a production build and packages `.output/` into an uploadable archive.

## 2. Version bumping

The version comes from `package.json` (`version`) unless overridden in the manifest. Bump
it before every store upload — stores reject re-uploads of an existing version.

```bash
npm version patch      # 0.1.0 → 0.1.1, also creates a git tag
```

Keep the version a plain `x.y.z` (Chrome allows up to four dot-separated integers; Firefox
is stricter — stick to `x.y.z`).

## 3. Store requirements

| Store | Needs |
| --- | --- |
| Chrome Web Store | Dev account ($5 one-time), zip, icons (16/32/48/128), screenshots, privacy disclosure |
| Firefox AMO | Free account, zip **+ sources zip** if minified, reviewer notes |
| Edge Add-ons | Free Partner Center account, zip, listing assets |

Provide icons in `public/icon/` (16, 32, 48, 128 px PNGs). Write an honest privacy/data-use
disclosure — broad `host_permissions` trigger deeper review.

## 4. Automated submission

WXT integrates with `web-ext` / publish tooling. Configure credentials as environment
variables and run:

```bash
wxt submit \
  --chrome-zip .output/*-chrome.zip \
  --firefox-zip .output/*-firefox.zip \
  --firefox-sources-zip .output/*-sources.zip \
  --edge-zip .output/*-edge.zip
```

Store credentials (Chrome `CLIENT_ID`/`CLIENT_SECRET`/`REFRESH_TOKEN`, AMO
`JWT_ISSUER`/`JWT_SECRET`, Edge `PRODUCT_ID`/API keys) live in env/secrets — never commit
them. Run `wxt submit init` to scaffold the config interactively.

## 5. CI release (GitHub Actions sketch)

```yaml
# .github/workflows/release.yml
on:
  push:
    tags: ['v*']
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: npm ci
      - run: npm run zip && npm run zip:firefox
      - run: npx wxt submit --chrome-zip .output/*-chrome.zip --firefox-zip .output/*-firefox.zip --firefox-sources-zip .output/*-sources.zip
        env:
          CHROME_CLIENT_ID: ${{ secrets.CHROME_CLIENT_ID }}
          CHROME_CLIENT_SECRET: ${{ secrets.CHROME_CLIENT_SECRET }}
          CHROME_REFRESH_TOKEN: ${{ secrets.CHROME_REFRESH_TOKEN }}
          # ...AMO / Edge secrets
```

## 6. Safari

Safari isn't a zip upload. Build, convert, and submit through Xcode / App Store Connect:

```bash
wxt build -b safari
xcrun safari-web-extension-converter .output/safari-mv3
# open the Xcode project, set signing, archive, submit via App Store Connect
```

## 7. Pre-submit checklist

- [ ] Version bumped; changelog/reviewer notes ready
- [ ] `npm run compile`, `npm run lint`, `npm test` all green
- [ ] Permissions minimised and justified in the listing
- [ ] Icons + screenshots + privacy disclosure prepared
- [ ] Firefox sources zip included; Safari converted and signed
- [ ] Store credentials in secrets, not committed
