# SG Affordability Engine — V4 Studio Edition

A responsive Singapore-focused affordability analysis web app, with a unified navigation/footer, animated ambient background, accessible scroll reveals, and distinct page designs.

## Run locally

Requirements: Node.js 20+, Python 3.10+. From this directory:

```bash
npm install
npm start
```

Open http://localhost:3000. The Node backend invokes Python via `PYTHON_BIN` (defaults to `python3`; set `PYTHON_BIN=python` on Windows if needed).

## Pages

- `/` — overview and quick-start options
- `/property.html` — property affordability
- `/vehicle.html` — car affordability and published COE data
- `/combined.html` — car + home monthly cost estimate
- `/compare.html` — saved scenarios in browser storage
- `/methodology.html` — model limitations and assumptions
- `/about.html` — project information

## Important limitations

Educational model, not a lender decision. Some financing constraints, CPF usage, lender-specific stress rates, and statutory fees may be simplified. COE data shows the latest **published completed bidding exercise**, not live intraday bidding, and depends on external data.gov.sg availability. Prices, taxes and rules must be independently verified.

## Tests

`npm test` executes the included JS and Python tests. Browser-level tests and deployment verification are still recommended.

## Property income validation fix
All numeric calculator inputs now use `step=any`, avoiding the browser step-mismatch error that rejected valid salaries (e.g. S$5,000) when `min=1` and `step=100`.

## v4.2 critical form fix
The Property calculator now serializes `existingLoans` and `ownedProperties` select options as JSON numbers, rather than strings. Previously, the Python engine rejected every property submission with the default dropdown values. Regression tests cover all nine dropdown combinations. Restart the server and hard-refresh your browser after replacing the previous version.


## v4.3 animation visibility update

- Corrected the ambient scene stacking order: previously `z-index:-1` could hide the animated layer behind the opaque body.
- Aurora/glow layer opacity: **50%**; grid opacity: **50%**.
- Animation duration reduced by half: 25→12.5 seconds, 30→15 seconds, 22→11 seconds, grid 38→19 seconds.
- Animation remains behind content and never blocks input interactions.
- Respects operating-system reduced-motion preferences.
- If changes are not visible, hard-refresh with Ctrl+Shift+R and check that reduced-motion is not enabled.


## Version 5 — Gradient Studio
Original Stripe-inspired visual hierarchy: animated gradient mesh, flowing contour ribbons, 50% background layer visibility, shared navigation and footer, mobile/tablet breakpoints, scroll reveals. No Stripe assets or branding used. Existing financial engine and API preserved.


## v5.1 Aurora Flow theme

All seven pages now share a midnight navy (#0B1220), electric indigo (#6366F1), mint (#2DD4BF) theme and a fixed, non-interactive animated aurora scene. Aurora layers use 50% opacity and 11–16-second motion cycles, with a reduced-motion fallback. The existing finance engine, APIs, and calculator logic are unchanged.

## Obsidian Gold design edition

All seven pages share an Obsidian Black / Champagne Gold / Warm Platinum theme. A more prominent animated gold aurora, sweeping metallic ribbons, luminous diagonal beams and orbital rings create a consistent decorative background. The animations are CSS-only, non-interactive and disabled for reduced-motion preferences. Core calculation code is unchanged from v5.1.


## Motion Studio enhancement

Added continuous cinematic gold mesh, slowly rotating light sweep, drifting gold dust, scroll reading progress, fine-pointer ambient glow, staggered scroll reveals, animated financial-chart tracing, premium button shine, animated gold result-card edge and understated card hover movement. Respects `prefers-reduced-motion`; purely visual effects do not change financial calculations or saved data.


## Balanced Pro motion update
- Balanced 14-second Obsidian Gold ambient motion, ~42% glow.
- Sequenced hero entrance, subtle same-site page transitions, refined input focus feedback.
- Animated calculator values, sticky live monthly summary, gold income gauge.
- Gold Chart.js charts and tooltips, loading shimmer, refined result transitions.
- Responsive and prefers-reduced-motion safeguards.
- Financial engine, API, scenario storage and original calculation logic remain unchanged.


## Editorial redesign (v6)
Every page uses a new Obsidian Gold editorial layout, page identity band, redesigned form/results surfaces, responsive navigation, premium typography and a consistent footer. Financial calculations, API endpoints, input IDs, scenario storage and motion scripts are retained from Balanced Pro.


## Atelier redesign (v7)
All seven pages feature a consistent editorial Obsidian Gold system: new chapter headers, numbered page identity, restrained cards, revised calculator workspaces, responsive navigation and balanced ambient motion. Existing financial logic is unchanged.
