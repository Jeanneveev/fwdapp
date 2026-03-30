# Best Practices Cleanup — fwdapp

**Date:** 2026-03-29
**Approach:** A — Extract and tidy (vanilla HTML/CSS/JS, no build tooling)

---

## Scope

Structural and polish cleanup of the existing fwdapp static site. No build system introduced. No header/nav deduplication across 19 HTML files (deferred — easier to batch-replace separately). No changes to `peptalks/` pages or personal stub pages (`adam.html`, etc.).

---

## Files to Create

### `scripts/config.js`
Single source of truth for all constants used across the app:
- `WIX_MAIN_SITE` — base URL for marylandforwardparty.com
- `TOKEN_KEY`, `TOKEN_EXPIRY_KEY`, `USER_KEY` — localStorage key names
- `PREVIEW_MANIFEST_PATH` — path to link-preview manifest JSON

Exported as named ES module exports so every script can `import` rather than redeclare.

### `scripts/auth.js`
The 155-line IIFE currently inline in `index.html`, extracted as an ES module:
- `import` constants from `config.js`
- All functions (`parseJwt`, `verifyToken`, `showLoggedIn`, `showLoggedOut`, `clearAuth`, `handleTokenFromUrl`, `checkAuthState`) remain unchanged in behaviour
- Loaded via `<script type="module" src="scripts/auth.js">` in index.html

---

## Files to Modify

### `index.html`
1. **Remove** the 155-line inline `<script>` block — replaced by `<script type="module" src="scripts/auth.js">`
2. **Remove** the 118-line inline `<style>` block — moved to `peptalks/styles.css`
3. **Add meta tags** in `<head>`:
   - `<meta name="description" content="...">`
   - `<meta property="og:title">`, `og:description`, `og:image`
   - `<meta name="theme-color" content="#...">`
4. **Fix `alt` attribute** on brand logo image (currently `alt=""`)
5. **Semantic HTML**: replace generic `<div>` wrappers with `<main>`, `<section>`, `<article>` where appropriate
6. **Add `lang="en"`** to `<html>` tag

### `peptalks/styles.css`
- Append the 118 lines of inline CSS moved from `index.html` (grid layout, card styles, auth UI styles, mobile breakpoints)
- No other changes — existing styles untouched

### `wix/requirements.txt` (new file)
Documents all Python dependencies for the thin-bridge server and tooling:
```
fastapi
httpx
pyjwt
uvicorn
playwright
beautifulsoup4
```

---

## What Is Not Changing

- `selectable_cards.js`, `link_preview_hover.js`, `reusableComponents.js` — left as-is
- All peptalks HTML pages — left as-is
- Personal stub pages — left as-is
- Root `index.html` project card markup — left as-is
- `wix/main.py` logic — left as-is

---

## Success Criteria

- `index.html` has zero inline `<script>` blocks and zero inline `<style>` blocks
- All constants referenced in `auth.js` come from `config.js` imports
- Page renders and auth flow works identically to before
- `wix/requirements.txt` exists and lists all deps
- Meta tags present and correct in `<head>`
