# Best Practices Cleanup — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract inline JS and CSS from `index.html` into proper ES modules and a shared stylesheet, add missing meta tags and semantic HTML, and document Python dependencies.

**Architecture:** Pure vanilla HTML/CSS/JS — no build tooling, no npm. Inline `<script>` becomes `<script type="module">` pointing to `scripts/auth.js`. All constants centralised in `scripts/config.js`. Inline `<style>` block moves to `peptalks/styles.css`.

**Tech Stack:** Vanilla JS ES modules, HTML5, CSS3. Python (FastAPI/uvicorn) for the wix/ bridge.

**Spec:** `docs/superpowers/specs/2026-03-29-best-practices-cleanup-design.md`

---

## Chunk 1: Config module + auth module

### Task 1: Create `scripts/config.js`

**Files:**
- Create: `scripts/config.js`

- [ ] **Step 1: Create the file with all shared constants**

```javascript
// scripts/config.js
// Central configuration for the FWD App.
// Import from this file rather than hardcoding values in individual scripts.

export const WIX_MAIN_SITE = 'https://www.marylandforwardparty.com';

// localStorage key names
export const TOKEN_KEY = 'wix_member_token';
export const TOKEN_EXPIRY_KEY = 'wix_token_expiry';
export const USER_KEY = 'wix_user';

// Link-preview manifest (relative to site root)
export const PREVIEW_MANIFEST_PATH = 'images/previews/link-preview-manifest.json';
```

- [ ] **Step 2: Verify the file exists and looks correct**

```bash
cat scripts/config.js
```

Expected: file prints cleanly with all five exports.

- [ ] **Step 3: Commit**

```bash
git add scripts/config.js
git commit -m "feat: add scripts/config.js with shared constants"
```

---

### Task 2: Create `scripts/auth.js`

**Files:**
- Create: `scripts/auth.js`
- Reference: `scripts/config.js` (import)

- [ ] **Step 1: Create the file**

Extract the auth logic from `index.html` lines 225–380, adapted to an ES module (constants replaced by imports from `config.js`, IIFE wrapper removed, `'wix_user'` hardcoded string replaced by the `USER_KEY` import):

```javascript
// scripts/auth.js
// Wix JWT authentication for the FWD App.
// Loaded as <script type="module"> from index.html.
// Flow: Wix Velo generates JWT -> redirect to ?token=<jwt> -> this module verifies and stores it.

import { WIX_MAIN_SITE, TOKEN_KEY, TOKEN_EXPIRY_KEY, USER_KEY } from './config.js';

const loginBtn = document.getElementById('wix-login-btn');
const logoutBtn = document.getElementById('wix-logout-btn');
const userMenu = document.getElementById('wix-user-menu');
const userName = document.getElementById('wix-user-name');

// Decode JWT payload (base64url → JSON). Does NOT verify the signature —
// HMAC verification requires the shared secret server-side.
function parseJwt(token) {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64).split('').map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join('')
    );
    return JSON.parse(jsonPayload);
  } catch (e) {
    console.error('Failed to parse JWT:', e);
    return null;
  }
}

// Validate expiry, issuer, and audience claims.
async function verifyToken(token) {
  const payload = parseJwt(token);
  if (!payload) return null;

  if (payload.exp && Date.now() >= payload.exp * 1000) {
    console.log('Token expired');
    return null;
  }
  if (payload.iss !== 'marylandforwardparty.com') {
    console.error('Token issuer mismatch:', payload.iss);
    return null;
  }
  if (payload.aud !== 'FWD.marylandforwardparty.com') {
    console.error('Token audience mismatch:', payload.aud);
    return null;
  }
  return payload;
}

function showLoggedIn(user) {
  loginBtn.style.display = 'none';
  userMenu.style.display = 'flex';
  userName.textContent = user.name || user.displayName || user.email || 'Member';
}

function showLoggedOut() {
  loginBtn.style.display = 'inline-block';
  userMenu.style.display = 'none';
}

function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(TOKEN_EXPIRY_KEY);
  localStorage.removeItem(USER_KEY);
}

async function handleTokenFromUrl() {
  const token = new URLSearchParams(window.location.search).get('token');
  if (!token) return false;

  const userInfo = await verifyToken(token);
  if (userInfo) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(TOKEN_EXPIRY_KEY, userInfo.exp || '');
    localStorage.setItem(USER_KEY, JSON.stringify(userInfo));
    window.history.replaceState({}, document.title, window.location.pathname + window.location.hash);
    showLoggedIn(userInfo);
    return true;
  }

  console.error('Invalid token received');
  clearAuth();
  return false;
}

async function checkAuthState() {
  const token = localStorage.getItem(TOKEN_KEY);
  const userJson = localStorage.getItem(USER_KEY);
  const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);

  if (token && userJson) {
    if (expiry && Date.now() >= parseInt(expiry) * 1000) {
      clearAuth();
      showLoggedOut();
      return;
    }
    const userInfo = await verifyToken(token);
    if (userInfo) {
      showLoggedIn(userInfo);
    } else {
      clearAuth();
      showLoggedOut();
    }
  } else {
    showLoggedOut();
  }
}

// Login: redirect to Wix login, return to the "Go to FWD App" button page.
loginBtn.addEventListener('click', () => {
  const returnUrl = encodeURIComponent(`${WIX_MAIN_SITE}/get-involved`);
  window.location.href = `${WIX_MAIN_SITE}/account/login?returnUrl=${returnUrl}`;
});

// Logout: clear local state.
logoutBtn.addEventListener('click', () => {
  clearAuth();
  showLoggedOut();
});

// Initialise on DOM ready.
document.addEventListener('DOMContentLoaded', async () => {
  const handledFromUrl = await handleTokenFromUrl();
  if (!handledFromUrl) await checkAuthState();
});
```

- [ ] **Step 2: Verify the file**

```bash
cat scripts/auth.js | head -5
```

Expected: shows the import line and opening comment.

- [ ] **Step 3: Commit**

```bash
git add scripts/auth.js
git commit -m "feat: extract inline auth script to scripts/auth.js ES module"
```

---

## Chunk 2: index.html — script, style, meta, and semantic cleanup

### Task 3: Remove inline `<script>` block and wire ES module

**Files:**
- Modify: `index.html` lines 222–381

- [ ] **Step 1: Replace the three `<script>` tags + inline script at the bottom of `<body>`**

Find this block (lines 222–381):
```html
    <script src="scripts/selectable_cards.js"></script>
    <script src="scripts/link_preview_hover.js"></script>
    <script src="peptalks/script.js"></script>
    <script>
      // Wix JWT Token Authentication Integration
      ... (155 lines) ...
    </script>
```

Replace with:
```html
    <script src="scripts/selectable_cards.js"></script>
    <script src="scripts/link_preview_hover.js"></script>
    <script src="peptalks/script.js"></script>
    <script type="module" src="scripts/auth.js"></script>
```

- [ ] **Step 2: Verify the inline script is gone**

```bash
grep -n "function parseJwt\|WIX_MAIN_SITE\|TOKEN_KEY" index.html
```

Expected: no output (constants and functions are now only in the external files).

- [ ] **Step 3: Open the page in a browser and confirm the auth UI still renders**

Open `index.html` directly (or via a local server). The header should show a "Log In" button. No console errors expected.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "refactor: replace inline auth script with <script type=module>"
```

---

### Task 4: Move inline `<style>` block to `peptalks/styles.css`

**Files:**
- Modify: `index.html` lines 9–117
- Modify: `peptalks/styles.css` (append)

- [ ] **Step 1: Append the inline CSS block to `peptalks/styles.css`**

The `<style>` block in `index.html` runs from line 9 (`<style>`) to line 117 (`</style>`) — 109 lines. Add a section comment followed by all the rules at the end of `peptalks/styles.css`:

```css

/* ─── index.html — project grid, auth UI, card styles ─────────────────────── */

.spotlight {
  border-color: var(--accent);
  background: linear-gradient(150deg, var(--accent-soft), var(--surface));
}

.brand.with-icon {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.brand-icon {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  object-fit: cover;
}

.project-title-link {
  color: inherit;
  text-decoration: none;
}

.project-title-link:hover {
  color: var(--accent);
}

.projects-grid {
  margin-top: 1.2rem;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
}

.grid-heading {
  margin-top: 1.4rem;
  margin-bottom: 0;
  background: linear-gradient(150deg, var(--accent-soft), var(--surface));
  border: 1px solid var(--accent);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 0.8rem 1rem;
}

.projects-grid > .card {
  grid-column: span 1;
  border-color: var(--accent);
  background: linear-gradient(150deg, var(--accent-soft), var(--surface));
}

.selectable-card {
  cursor: pointer;
  transition: box-shadow 140ms ease, transform 140ms ease;
}

.selectable-card.is-highlighted {
  box-shadow:
    0 0 0 2px rgba(255, 255, 255, 0.92),
    0 14px 32px rgba(255, 255, 255, 0.5);
  transform: translateY(-1px);
}

.project-preview {
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  border-radius: 10px;
  border: 1px solid var(--line);
  margin: 0.25rem 0 0.7rem;
  background: var(--surface-alt);
}

@media (max-width: 840px) {
  .projects-grid {
    grid-template-columns: 1fr;
  }
}

.wix-auth-container {
  display: flex;
  align-items: center;
  margin-left: 1rem;
}

.wix-user-menu {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

#wix-user-name {
  color: var(--text);
  font-size: 0.9rem;
}

.btn-small {
  padding: 0.4rem 0.8rem;
  font-size: 0.85rem;
}

@media (max-width: 720px) {
  .wix-auth-container {
    margin-left: 0;
    margin-top: 0.5rem;
  }
}
```

- [ ] **Step 2: Remove the `<style>` block from `index.html`**

Delete lines 9–117 (the entire `<style>...</style>` block). The `<link rel="stylesheet" href="peptalks/styles.css">` line on line 8 already loads the stylesheet, so the styles will still apply.

- [ ] **Step 3: Verify no inline styles remain**

```bash
grep -n "<style>" index.html
```

Expected: no output.

- [ ] **Step 4: Open in browser, confirm the grid layout and card styles still look correct**

The projects grid should still render in 3 columns on desktop and 1 column on mobile.

- [ ] **Step 5: Commit**

```bash
git add index.html peptalks/styles.css
git commit -m "refactor: move inline CSS to peptalks/styles.css"
```

---

### Task 5: Meta tags, semantic HTML, and accessibility fixes

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Add meta tags to `<head>`**

After the existing `<meta name="viewport">` line, insert:

```html
    <meta name="description" content="Civic tech projects from the Maryland Forward Party — tools for transparency, participation, and democratic reform." />
    <meta name="author" content="Maryland Forward Party" />
    <meta name="theme-color" content="#6a3cb5" />
    <meta property="og:title" content="MD Forward Party — Civic Tech" />
    <meta property="og:description" content="Open-source civic tech tools built by the Maryland Forward Party." />
    <meta property="og:image" content="images/favicon.png" />
    <meta property="og:type" content="website" />
```

- [ ] **Step 2: Fix the empty `alt` on the brand icon**

Find:
```html
<img class="brand-icon" src="images/favicon.png" alt="" />
```

Replace with:
```html
<img class="brand-icon" src="images/favicon.png" alt="MD Forward Party logo" />
```

- [ ] **Step 3: Verify `lang="en"` and semantic HTML are already in place**

`index.html` line 2 already has `<html lang="en">`. Confirm both that and the semantic structure:

```bash
grep -n 'lang="en"\|<main\|<section\|<article\|<header\|<footer' index.html
```

Expected: `lang="en"` on line 2, and at least one match each for `<main>`, `<section>`, `<article>`, `<header>`, `<footer>`. No further changes needed.

- [ ] **Step 4: Add `aria-label` to the login and logout buttons**

Find:
```html
<button id="wix-login-btn" class="btn btn-small" style="display: none;">Log In</button>
```
Replace with:
```html
<button id="wix-login-btn" class="btn btn-small" style="display: none;" aria-label="Log in via Maryland Forward Party">Log In</button>
```

Find:
```html
<button id="wix-logout-btn" class="btn btn-small">Log Out</button>
```
Replace with:
```html
<button id="wix-logout-btn" class="btn btn-small" aria-label="Log out of FWD App">Log Out</button>
```

- [ ] **Step 5: Verify `<head>` has all new meta tags**

```bash
grep -n "og:title\|theme-color\|description" index.html
```

Expected: 5–6 matching lines.

- [ ] **Step 6: Commit**

```bash
git add index.html
git commit -m "fix: add meta tags, fix empty alt, add aria-labels to auth buttons"
```

---

## Chunk 3: Python dependency documentation

### Task 6: Create `wix/requirements.txt`

**Files:**
- Create: `wix/requirements.txt`

- [ ] **Step 1: Create the file**

```
# wix/requirements.txt
# Dependencies for the Wix OAuth thin-bridge server (wix/main.py)
# and the project preview generation script (scripts/generate_project_previews.py).
#
# Install: pip install -r wix/requirements.txt
# Then for Playwright: playwright install chromium

fastapi>=0.110.0
uvicorn[standard]>=0.29.0
httpx>=0.27.0
pyjwt>=2.8.0
beautifulsoup4>=4.12.0
playwright>=1.43.0
```

- [ ] **Step 2: Verify**

```bash
cat wix/requirements.txt
```

Expected: 6 dependency lines with version pins.

- [ ] **Step 3: Commit**

```bash
git add wix/requirements.txt
git commit -m "chore: add wix/requirements.txt for Python dependencies"
```

---

## Chunk 4: Final verification

### Task 7: End-to-end smoke test

- [ ] **Step 1: Confirm `index.html` has zero inline `<script>` blocks**

```bash
grep -c "<script>" index.html
```

Expected: `4` (three `<script src=...>` tags plus one `<script type=module>` — all external, none with inline code).

Actually run:
```bash
grep -n "^    <script>" index.html
```
Expected: 4 lines, all `<script src=` or `<script type=module`, none with inline code following them.

- [ ] **Step 2: Confirm `index.html` has zero inline `<style>` blocks**

```bash
grep -c "<style>" index.html
```

Expected: `0`

- [ ] **Step 3: Confirm config.js exports are used in auth.js**

```bash
grep "import.*config" scripts/auth.js
```

Expected: `import { WIX_MAIN_SITE, TOKEN_KEY, TOKEN_EXPIRY_KEY, USER_KEY } from './config.js';`

- [ ] **Step 4: Open `index.html` in a browser via a local server**

```bash
python3 -m http.server 8080
```

Visit `http://localhost:8080`. Confirm:
- Page renders correctly (grid, cards, styles intact)
- "Log In" button appears in header
- Browser console has no errors

- [ ] **Step 5: Final commit if any loose changes remain**

```bash
git status
git add -p   # review and stage any remaining changes
git commit -m "chore: best practices cleanup complete"
```
