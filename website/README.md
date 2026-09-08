# OMH public guide

Static Astro documentation and presentation site for GitHub Pages. The eight Markdown chapters in
`src/content/` are the single content source for reader and presentation modes.

## Language and editorial contract

Public-facing prose is **pt-BR**, an explicitly approved exception for this Portuguese-language video
guide. Source identifiers, code comments, tests, configuration, and this maintenance documentation
remain English. Do not publish private transcripts, credentials, employer references, or unsupported
claims of behavioral superiority. Chapter sources are pinned to the audited product revision.

## Local development

Use Node.js 24 and npm. From `website/`:

```sh
npm ci
npm run dev
```

Open `http://127.0.0.1:4321/oh-my-harness/`. Fonts are packaged locally; no analytics, runtime API,
remote font service, login, or external site-hosting provider is required.

## Verification

```sh
npm run format
npm run lint
npm run check
npm run build
npx playwright install chromium
npm test
```

Browser tests cover reader mode, presentation state, chapter URLs, keyboard navigation, native
details, camera space, three viewport sizes, and no-JavaScript rendering. They do not evaluate OMH
agent behavior. Review screenshots manually before changing the visual system.

## Recording

Choose **Apresentar** or open `?present=1#knowledge` for a chapter-specific retake. Left/right arrows
navigate when focus is outside native controls. **R** reveals the diagram; **Escape** exits from any
control. Buttons provide the same actions without shortcuts. Notes are **visible on the page and
in screen recordings**; they are not a private presenter window. Camera space reserves the right
side on desktop; it does not access a camera. The page remains scrollable for deep dives, smaller
viewports, and enlarged text. Hide notes and camera guides before clean takes if needed.

Reader mode works without JavaScript. Presentation mode intentionally requires JavaScript. The
site is not a transcript player or a claim that the demonstration steps were executed.

## Publication

The Pages workflow checks and builds pull requests, and publishes only pushes to `master`.
Configure repository Settings → Pages → Source as **GitHub Actions**. The canonical base path is
`/oh-my-harness`; changing the repository name requires updating Astro configuration and browser
test URLs together. Deployment uses the reviewed build artifact, not a separate hosting project.

Roll back by reverting the website change and letting the same workflow deploy the previous site.
There is no database or server-side migration. The initial site requires a merge before its first
production deployment; opening a PR does not publish it.
