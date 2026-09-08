const chapters = Array.from(
  document.querySelectorAll<HTMLElement>("[data-chapter]"),
);
const links = Array.from(
  document.querySelectorAll<HTMLAnchorElement>("[data-chapter-link]"),
);

function required<T extends HTMLElement>(id: string): T {
  const element = document.getElementById(id);
  if (!element) throw new Error(`Missing presentation control: ${id}`);
  return element as T;
}

const present = required<HTMLButtonElement>("present");
const controls = required("presentation-controls");
const previous = required<HTMLButtonElement>("previous");
const next = required<HTMLButtonElement>("next");
const reveal = required<HTMLButtonElement>("reveal");
const notes = required<HTMLButtonElement>("notes");
const camera = required<HTMLButtonElement>("camera");
const guide = required("camera-guide");
let presenting = false;
let current = 0;
let revealed = false;
let showNotes = false;
let cameraSpace = false;
const detailState = new Map<HTMLDetailsElement, boolean>();

function hashIndex(): number {
  return Math.max(
    0,
    chapters.findIndex((chapter) => `#${chapter.id}` === location.hash),
  );
}

function update(): void {
  document.body.classList.toggle("presenting", presenting);
  document.body.classList.toggle("camera-space", presenting && cameraSpace);
  controls.hidden = !presenting;
  guide.hidden = !presenting || !cameraSpace;
  chapters.forEach((chapter, index) => {
    chapter.hidden = presenting && index !== current;
    chapter.classList.toggle("revealed", revealed);
    const note = chapter.querySelector<HTMLElement>(".speaker-note");
    if (note) note.hidden = !presenting || !showNotes;
  });
  links.forEach((link, index) => {
    if (index === current) link.setAttribute("aria-current", "location");
    else link.removeAttribute("aria-current");
  });
  previous.disabled = current === 0;
  next.disabled = current === chapters.length - 1;
  required("progress").textContent =
    `${String(current + 1).padStart(2, "0")} / ${String(chapters.length).padStart(2, "0")}`;
  reveal.setAttribute("aria-pressed", String(revealed));
  reveal.textContent = revealed ? "Ocultar diagrama" : "Revelar diagrama";
  notes.setAttribute("aria-pressed", String(showNotes));
  camera.setAttribute("aria-pressed", String(cameraSpace));
}

function select(index: number, focus: boolean, writeHistory = true): void {
  current = Math.max(0, Math.min(chapters.length - 1, index));
  revealed = false;
  update();
  const chapter = chapters[current];
  if (!chapter) return;
  if (writeHistory && location.hash !== `#${chapter.id}`)
    history.pushState(null, "", `#${chapter.id}`);
  if (presenting) window.scrollTo(0, 0);
  if (focus)
    chapter
      .querySelector<HTMLElement>("h1, h2")
      ?.focus({ preventScroll: true });
}

function togglePresentation(enable: boolean, writeHistory = true): void {
  const modeChanged = presenting !== enable;
  presenting = enable;
  const url = new URL(location.href);
  if (enable) url.searchParams.set("present", "1");
  else url.searchParams.delete("present");
  if (writeHistory) history.replaceState(null, "", url);
  if (modeChanged)
    document
      .querySelectorAll<HTMLDetailsElement>(".deep-dive")
      .forEach((detail) => {
        if (enable) {
          detailState.set(detail, detail.open);
          detail.open = false;
        } else detail.open = detailState.get(detail) ?? true;
      });
  select(current, enable, writeHistory);
  if (!enable && modeChanged) {
    chapters[current]?.scrollIntoView();
    present.focus({ preventScroll: true });
  }
}

present.hidden = false;
present.addEventListener("click", () => togglePresentation(true));
required("exit").addEventListener("click", () => togglePresentation(false));
previous.addEventListener("click", () => select(current - 1, true));
next.addEventListener("click", () => select(current + 1, true));
reveal.addEventListener("click", () => {
  revealed = !revealed;
  update();
});
notes.addEventListener("click", () => {
  showNotes = !showNotes;
  update();
});
camera.addEventListener("click", () => {
  cameraSpace = !cameraSpace;
  update();
});
function restoreLocation(): void {
  current = hashIndex();
  const enable = new URLSearchParams(location.search).get("present") === "1";
  togglePresentation(enable, false);
}

window.addEventListener("hashchange", restoreLocation);
window.addEventListener("popstate", restoreLocation);
document.addEventListener("keydown", (event: KeyboardEvent) => {
  if (
    !presenting ||
    event.altKey ||
    event.ctrlKey ||
    event.metaKey ||
    event.shiftKey
  )
    return;
  if (
    event.target instanceof HTMLElement &&
    event.target.closest(
      "input, textarea, select, [contenteditable], button, summary, a",
    )
  )
    return;
  const actions: Record<string, () => void> = {
    ArrowRight: () => select(current + 1, true),
    ArrowLeft: () => select(current - 1, true),
    r: () => {
      revealed = !revealed;
      update();
    },
  };
  const action = actions[event.key];
  if (action) {
    event.preventDefault();
    action();
  }
});
// Escape is a global exit even when a native control owns keyboard focus.
document.addEventListener("keydown", (event: KeyboardEvent) => {
  if (presenting && event.key === "Escape") togglePresentation(false);
});
const observer = new IntersectionObserver(
  (entries) => {
    if (presenting) return;
    const entry = entries.find((item) => item.isIntersecting);
    if (!entry) return;
    current = chapters.indexOf(entry.target as HTMLElement);
    update();
  },
  { rootMargin: "-15% 0px -65% 0px" },
);
chapters.forEach((chapter) => observer.observe(chapter));
restoreLocation();
