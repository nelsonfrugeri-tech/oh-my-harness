# Design System — Analysis Site Visual Standard

This is the **visual contract**. A site generated today and one generated six months from now
must be recognizable as the same product. Everything here can be copied directly into the
`<style>` block of `index.html`.

The canonical reference artifact is `assets/skeleton.html`. Start from it instead of building
from scratch.

---

## 1 · Tokens

Complete `:root` block. **Copy it in full**; remove only tokens the site does not use.

```css
:root{
  color-scheme: dark;
  /* surfaces */
  --page:#0d0d0d; --surface:#1a1a19; --surface-2:#212120;
  /* text */
  --ink:#ffffff; --ink-2:#c3c2b7; --ink-3:#898781;
  /* structure */
  --grid:#2c2c2a; --baseline:#383835; --ring:rgba(255,255,255,.10);
  /* categorical — 8 canonical frozen slots for dark mode */
  --s1:#3987e5; --s2:#d95926; --s3:#199e70; --s4:#c98500;
  --s5:#d55181; --s6:#008300; --s7:#9085e9; --s8:#e66767;
  /* status — reserved, NEVER used as a data series */
  --st-good:#0ca30c; --st-warn:#fab219; --st-serious:#ec835a; --st-crit:#d03b3b;
  --mono:ui-monospace,SFMono-Regular,Menlo,monospace;
}
```

### The hard rule: fixed color per entity

A categorical slot is assigned to **one domain entity** (an agent, service, team, or module),
and that color **never changes anywhere on the site**: not in SVG diagrams, tables, chips,
cards, or matrices. This keeps reading inexpensive: the reader learns the color once in the
hero and then recognizes it everywhere.

Give the token a semantic alias; never use its slot number in the site body:

```css
--c-orch:var(--s1);    /* orchestrator */
--c-diag:var(--s3);    /* diagnosis-expert */
```

**Color follows the entity, never its rank.** Do not recolor by importance, alphabetical order,
or table position.

### Slot allocation order

Use slots in `--s1 → --s8` order. Beyond eight entities, **do not invent another hue**: group
minor entities as "other" (gray `--ink-3`) or split them into two sections with separate legends.

### Status is never a series

`--st-*` means health or severity (good, warning, serious, critical), and nothing else. An entity
never receives a status color, and a status never receives a categorical color. Status must
always be **paired with an icon or label** because color alone cannot carry meaning.

### Canonical frozen palette

The bundled categorical and status colors are the canonical, frozen palette for this skill.
Use them unchanged and record that provenance in the footer. A palette change is a design-system
revision: update this reference and the skeleton together, provide contrast and color-vision
evidence in the review, and treat the change as intentionally breaking visual consistency.

---

## 2 · Typography and Layout Foundation

```css
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--page);color:var(--ink-2);
  font:15px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif;}
h1,h2,h3,h4{color:var(--ink);line-height:1.25;font-weight:650}
h1{font-size:30px;margin:0 0 8px}
h2{font-size:22px;margin:0 0 6px;scroll-margin-top:76px}
h3{font-size:16px;margin:22px 0 8px}
p{margin:8px 0}
a{color:var(--s1);text-decoration:none} a:hover{text-decoration:underline}
code{font-family:var(--mono);font-size:.86em;background:var(--surface-2);
  border:1px solid var(--ring);border-radius:5px;padding:1px 5px;color:var(--ink-2)}
section{max-width:1180px;margin:0 auto;padding:34px 28px 6px}
.lead{font-size:16.5px;color:var(--ink-2);max-width:900px}
.muted{color:var(--ink-3)} .small{font-size:13px}
.kicker{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-3);margin-bottom:6px}
.divider{border:0;border-top:1px solid var(--grid);max-width:1180px;margin:26px auto}
svg text{font-family:system-ui,-apple-system,"Segoe UI",sans-serif}
```

Rules: use the **system font** (zero webfonts and zero external requests), keep a maximum reading
width of `1180px`, and apply `scroll-margin-top` to `h2` so the sticky navigation does not cover
anchored headings.

### Offline security boundary

Keep the skeleton's Content Security Policy unchanged. It denies all resources by default,
permits only the bundled inline style and scrollspy, allows data images, and explicitly blocks
network connections, base-URL changes, and form submission:

```html
<meta http-equiv="Content-Security-Policy"
      content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; connect-src 'none'; base-uri 'none'; form-action 'none'">
```

HTML-escape every string derived from source code, repository files, tool output, or user input
before inserting it into the DOM. This applies to text nodes and attribute values, including SVG
labels and `aria-label`. Never interpolate untrusted content into markup or inline JavaScript.

---

## 3 · Component Catalog

Each component has an informational role. Choose components by role, not appearance.

| Component | Role | When to use |
|---|---|---|
| sticky `nav` + scrollspy | orientation | always; analysis sites are long by nature |
| hero (kicker + h1 + lead + chips + tiles) | BLUF | always; open with the conclusion |
| `.tile` | magnitude | 4–8 numbers that establish system scale |
| `.chip` / `.chip.mono` | metadata | version, commit, date, parameter |
| `.card` | reading unit | any self-contained block |
| `.card.agent` | component profile | one per domain entity |
| `.kv` (`dl`) | exact parameters | model, timeout, limits, and other facts |
| `.flow` | short sequence | a pipeline of 3–6 steps |
| `.stack` (`ol`) | sourced numbered sequence | step-by-step flow citing `file:line` |
| `table` | tabular fact | any comparison |
| `table.matrix` | X×Y relationship | usage, coverage, support |
| `.tl` | history | timeline of decisions and merge requests |
| `<details>` | progressive disclosure | fine detail that cannot be omitted |
| `.badge` | inline qualifier | `gate`, `inline`, `max` |
| `.legend` | color dictionary | directly below the hero tiles |
| `footer` | provenance | `file:line` sources + date + commit |

### nav sticky + scrollspy

```css
nav{position:sticky;top:0;z-index:50;background:#111110;border-bottom:1px solid var(--grid)}
nav .in{max-width:1180px;margin:0 auto;display:flex;gap:4px;align-items:center;
  padding:10px 28px;overflow-x:auto;white-space:nowrap}
nav .brand{color:var(--ink);font-weight:700;margin-right:14px;font-size:14px}
nav a{color:var(--ink-3);font-size:13px;padding:5px 9px;border-radius:6px}
nav a:hover{color:var(--ink);background:var(--surface);text-decoration:none}
nav a.on{color:var(--ink);background:var(--surface)}
```

```html
<script>
  const links=[...document.querySelectorAll('nav a')];
  const secs=links.map(a=>document.querySelector(a.hash)).filter(Boolean);
  const spy=()=>{const y=scrollY+90;let cur=secs[0];
    for(const s of secs){if(s.offsetTop<=y)cur=s}
    links.forEach(a=>a.classList.toggle('on',a.hash==='#'+cur.id))};
  addEventListener('scroll',spy,{passive:true});spy();
</script>
```

This is the **only** JavaScript allowed by default. An analysis site has no application state.

### Surfaces and grid

```css
.card{background:var(--surface);border:1px solid var(--ring);border-radius:12px;padding:18px 20px;margin:14px 0}
.grid{display:grid;gap:14px}
.cols-2{grid-template-columns:repeat(auto-fit,minmax(340px,1fr))}
.cols-3{grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.cols-4{grid-template-columns:repeat(auto-fit,minmax(200px,1fr))}
```

`auto-fit` + `minmax` provide responsiveness without media queries. The site must work on mobile.

### Stat tiles

```css
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(128px,1fr));gap:10px;margin:18px 0}
.tile{background:var(--surface);border:1px solid var(--ring);border-radius:10px;padding:12px 14px}
.tile b{display:block;font-size:26px;color:var(--ink);font-weight:700}
.tile span{font-size:12.5px;color:var(--ink-3)}
```

```html
<div class="tiles">
  <div class="tile"><b>5</b><span>specialized experts</span></div>
</div>
```

Put the number first and the label second. A tile is always a **verified count**, never an
estimate. If it was not counted, it does not belong in a tile.

### Chips e dots

```css
.chip{display:inline-block;font-size:12px;border:1px solid var(--ring);border-radius:999px;
  padding:2px 10px;margin:2px 4px 2px 0;background:var(--surface-2);color:var(--ink-2)}
.chip.mono{font-family:var(--mono);font-size:11.5px}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px;vertical-align:baseline}
```

The `.dot` is an **identity stamp**: whenever an entity appears in a table, cell, or list item,
its dot precedes it. This carries the entity color throughout the site.

### Tables

```css
table{width:100%;border-collapse:collapse;margin:10px 0;font-size:13.5px}
th{color:var(--ink-3);font-weight:600;text-align:left;font-size:12px;
  text-transform:uppercase;letter-spacing:.06em;border-bottom:1px solid var(--baseline);padding:7px 10px}
td{border-bottom:1px solid var(--grid);padding:7px 10px;vertical-align:top;color:var(--ink-2)}
tr:last-child td{border-bottom:0}
td.num,.tnum{font-variant-numeric:tabular-nums;font-family:var(--mono);font-size:12.5px}
.tscroll{overflow-x:auto}
/* X×Y matrix */
.matrix td:not(:first-child),.matrix th:not(:first-child){text-align:center}
.cell-off{color:var(--grid)}
```

**Every table belongs inside `<div class="tscroll">`**. Without it, the table overflows on
mobile. Put numbers in `.tnum`/`td.num`; tabular numerals align the columns.

In a matrix, a filled cell is `●`; an empty cell is `—` with `class="cell-off"`. Empty must be
visibly empty, not absent.

### Component profile (`.agent`)

An entity profile has a color bar at the top, a dot in the title, a one-line sourced role,
exact parameters in `dl.kv`, a layer stack in `ol.stack`, and detail in `<details>`.

```css
.agent{border-top:3px solid var(--ac,var(--baseline))}
.agent h3{margin:2px 0 2px;display:flex;align-items:center;gap:8px;font-size:17px}
.agent .role{color:var(--ink-3);font-size:13px;margin-bottom:10px}
.kv{display:grid;grid-template-columns:auto 1fr;gap:3px 14px;font-size:13px;margin:10px 0}
.kv dt{color:var(--ink-3)} .kv dd{margin:0;color:var(--ink-2)}
```

```html
<div class="card agent" style="--ac:var(--c-orch)">
  <h3><span class="dot" style="background:var(--c-orch)"></span>name — role in three words</h3>
  <div class="role">What it does in one sentence · <code>src/path/file.py:69-139</code></div>
  <dl class="kv">
    <dt>Model</dt><dd><span class="chip mono">gemini-3.5-flash</span> timeout <span class="tnum">180s</span></dd>
  </dl>
</div>
```

### Flow and stack

```css
.flow{display:flex;flex-wrap:wrap;align-items:stretch;gap:8px;margin:12px 0}
.flow .step{background:var(--surface-2);border:1px solid var(--ring);border-radius:9px;
  padding:9px 12px;font-size:13px;min-width:120px;flex:1}
.flow .step b{display:block;color:var(--ink);font-size:13px;margin-bottom:2px}
.flow .arr{align-self:center;color:var(--ink-3);font-size:16px}
.stack{counter-reset:mw;margin:8px 0;padding:0;list-style:none}
.stack li{counter-increment:mw;border:1px solid var(--grid);border-radius:8px;
  background:var(--surface-2);padding:7px 12px 7px 40px;margin:6px 0;position:relative;font-size:13.5px}
.stack li::before{content:counter(mw);position:absolute;left:12px;top:7px;color:var(--ink-3);
  font-family:var(--mono);font-size:12px}
.stack li b{color:var(--ink)}
.stack li .hook{float:right;color:var(--ink-3);font-family:var(--mono);font-size:11.5px}
```

Use `.flow` for sequences without strong numbering (3–6 boxes separated by `→`). Use `.stack`
when order matters and each step has a source; the right-aligned `<span class="hook">` carries
the `file:line` reference.

### Progressive disclosure

```css
details{margin:10px 0;border:1px solid var(--grid);border-radius:8px;background:var(--surface-2)}
details summary{cursor:pointer;padding:8px 12px;color:var(--ink);font-size:13.5px;font-weight:600}
details[open] summary{border-bottom:1px solid var(--grid)}
details .body{padding:10px 14px}
details ul{margin:4px 0;padding-left:18px} details li{margin:4px 0;font-size:13.5px}
```

The `<summary>` is a **specific promise** ("Output contract — DiagnosisOutput"), never
"More details." Its text lets the reader decide whether to expand it.

### Timeline

```css
.tl{border-left:2px solid var(--baseline);margin:14px 0 8px 8px;padding-left:22px}
.tl .ev{position:relative;margin:0 0 18px}
.tl .ev::before{content:"";position:absolute;left:-28px;top:5px;width:10px;height:10px;
  border-radius:50%;background:var(--ink-3)}
.tl .ev.hi::before{background:var(--s1)}
.tl .ev b{color:var(--ink)}
.tl .date{font-family:var(--mono);font-size:12px;color:var(--ink-3)}
```

`.hi` marks **the event that explains the present**. Use no more than one or two per timeline.

### Badges and legend

```css
.badge{font-size:11px;border-radius:5px;padding:2px 7px;font-weight:600}
/* Each badge uses its entity/status color with ~12% background and ~40% border. */
.badge.gate{background:rgba(250,178,25,.10);color:var(--st-warn);border:1px solid rgba(250,178,25,.35)}
.legend{display:flex;flex-wrap:wrap;gap:12px;margin:12px 0}
.legend span{font-size:13px}
footer{max-width:1180px;margin:30px auto 0;padding:22px 28px 42px;border-top:1px solid var(--grid);
  color:var(--ink-3);font-size:13px}
```

---

## 4 · System-Level SVG Diagram

Use one per site, in the first section after the hero. Rules:

- Use an **inline SVG** with a `viewBox` and never fixed `width`/`height`; it then scales on its
  own. Place it inside `<div class="card" style="padding:10px">`.
- Add `role="img"` and an `aria-label` that describes the diagram.
- Use **literal hex values inside SVG**, not `var(--token)`. This matches the reference artifact
  and survives headless rendering, `file://`, and PDF export reliably. Keep each entity's hex
  identical to its token value; maintain that coupling when authoring the diagram.
- Declare the arrow marker once in `<defs>`:

```html
<defs>
  <marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7"
          orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#898781"/></marker>
</defs>
```

- Entity box: `fill="#1a1a19"` + `stroke="<entity hex>"` + `stroke-width="2"`. Neutral or
  infrastructure box: `fill="#212120"` or `#161615`, with `stroke="rgba(255,255,255,.12)"`.
- Text: title `13–14px fill="#fff"`, body `11.5–12px fill="#c3c2b7"`, note
  `11px fill="#898781"`. Nothing may be smaller than 11px.
- A dashed line (`stroke-dasharray="4 4"`) means a secondary or cross-cutting relationship; a
  solid line means the main flow.
- **Layout arithmetic is your responsibility** because SVG has no automatic layout. Calculate
  `x/y/width/height`, then verify in a screenshot that nothing collides or escapes the `viewBox`.
- Directly below the SVG card, add `<p class="small muted">Sources: <code>…</code></p>`.

---

## 5 · Anti-Patterns

| Do not | Why |
|---|---|
| Add a framework, CDN, webfont, or remote icon | it breaks self-contained and offline operation |
| Insert source-derived text without HTML escaping | it can create executable markup despite the offline boundary |
| Add a color outside the eight frozen slots | it breaks the canonical palette contract |
| Recolor the same entity between sections | it destroys the primary low-cost reading mechanism |
| Give an entity a status color | status becomes noise and the series becomes a false alarm |
| Put a table outside `.tscroll` | it overflows on mobile |
| Use a generic `<details>` summary | the reader cannot decide whether to open it |
| Use a long paragraph for tabular data | the data shape calls for a table |
| Show an unsourced number | analysis without `file:line` evidence is opinion |
| Add gradients, colored shadows, or animation | it adds noise to a sober, dense standard |
