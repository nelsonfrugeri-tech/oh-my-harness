export {};

const sceneElements = Array.from(
  document.querySelectorAll<HTMLElement>("[data-scene]"),
);
const previous = document.querySelector<HTMLButtonElement>(
  "#narrative-previous",
);
const next = document.querySelector<HTMLButtonElement>("#narrative-next");
const selection =
  document.querySelector<HTMLSelectElement>("#narrative-select");
const counter = document.querySelector<HTMLElement>("#narrative-count");
const progress = document.querySelector<HTMLElement>("#narrative-progress-bar");
const announcement = document.querySelector<HTMLElement>(
  "#narrative-announcement",
);
let activeIndex = 0;

function announce(message: string): void {
  if (announcement) announcement.textContent = message;
}

function hashIndex(): number {
  const index = sceneElements.findIndex(
    (scene) => `#${scene.id}` === window.location.hash,
  );
  return index < 0 ? 0 : index;
}

function showScene(index: number, moveFocus = false): void {
  const scene = sceneElements[index];
  if (!scene) return;
  activeIndex = index;
  sceneElements.forEach((element, sceneIndex) => {
    element.hidden = sceneIndex !== index;
  });
  if (previous) previous.disabled = index === 0;
  if (next) next.disabled = index === sceneElements.length - 1;
  if (selection) selection.value = scene.id;
  if (counter)
    counter.textContent = `${String(index + 1).padStart(2, "0")} / ${sceneElements.length}`;
  if (progress)
    progress.style.width = `${((index + 1) / sceneElements.length) * 100}%`;
  const title = scene.querySelector<HTMLElement>("h1, h2");
  announce(
    `Cena ${index + 1} de ${sceneElements.length}: ${title?.textContent ?? ""}`,
  );
  if (moveFocus) title?.focus({ preventScroll: true });
  window.scrollTo({ top: 0, behavior: "instant" });
}

function navigate(index: number, moveFocus = false): void {
  const scene = sceneElements[index];
  if (!scene) return;
  if (window.location.hash !== `#${scene.id}`)
    window.history.pushState(null, "", `#${scene.id}`);
  showScene(index, moveFocus);
}

function handleKeys(event: KeyboardEvent): void {
  if (
    event.defaultPrevented ||
    event.altKey ||
    event.ctrlKey ||
    event.metaKey ||
    event.shiftKey
  )
    return;
  const target = event.target;
  if (
    target instanceof Element &&
    target.closest(
      "input, textarea, select, button, a, summary, [contenteditable]:not([contenteditable='false']), [role='textbox']",
    )
  )
    return;
  const destinations: Record<string, number> = {
    ArrowLeft: activeIndex - 1,
    PageUp: activeIndex - 1,
    ArrowRight: activeIndex + 1,
    PageDown: activeIndex + 1,
    Home: 0,
    End: sceneElements.length - 1,
  };
  const index = destinations[event.key];
  if (index === undefined) return;
  event.preventDefault();
  navigate(index, true);
}

function initializeTheme(): void {
  const button = document.querySelector<HTMLButtonElement>("#narrative-theme");
  if (!button) return;
  button.hidden = false;
  button.addEventListener("click", () => {
    const root = document.documentElement;
    const dark =
      root.dataset.theme === "dark" ||
      (!root.dataset.theme &&
        window.matchMedia("(prefers-color-scheme: dark)").matches);
    const theme = dark ? "light" : "dark";
    root.dataset.theme = theme;
    button.title = `Tema ${theme === "dark" ? "escuro" : "claro"} · alternar`;
    try {
      localStorage.setItem("omh-theme", theme);
    } catch {
      /* Theme still works for this page. */
    }
    announce(`Tema ${theme === "dark" ? "escuro" : "claro"} ativado.`);
  });
}

function initializeFullscreen(): void {
  const button = document.querySelector<HTMLButtonElement>(
    "#narrative-fullscreen",
  );
  if (!button || !document.fullscreenEnabled) return;
  button.hidden = false;
  button.addEventListener("click", async () => {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await document.documentElement.requestFullscreen();
    } catch {
      announce(
        "A tela cheia não está disponível. A apresentação continua nesta janela.",
      );
    }
  });
  document.addEventListener("fullscreenchange", () => {
    const label = document.fullscreenElement
      ? "Sair da tela cheia"
      : "Tela cheia";
    button.setAttribute("aria-label", label);
    button.title = label;
  });
}

function initializeCamera(): void {
  const button = document.querySelector<HTMLButtonElement>("#narrative-camera");
  if (!button) return;
  button.hidden = false;
  button.addEventListener("click", () => {
    const reserved = document.body.classList.toggle("camera-space");
    button.setAttribute("aria-pressed", String(reserved));
    announce(
      reserved
        ? "Espaço para câmera reservado em telas largas."
        : "Espaço para câmera desativado.",
    );
  });
}

if (sceneElements.length && previous && next && selection) {
  document.body.dataset.narrativeReady = "true";
  const controls = document.querySelector<HTMLElement>(".narrative-controls");
  if (controls) controls.hidden = false;
  previous.addEventListener("click", () => navigate(activeIndex - 1, true));
  next.addEventListener("click", () => navigate(activeIndex + 1, true));
  selection.addEventListener("change", () =>
    navigate(sceneElements.findIndex((scene) => scene.id === selection.value)),
  );
  document.addEventListener("keydown", handleKeys);
  document.addEventListener("click", (event) => {
    const link =
      event.target instanceof Element
        ? event.target.closest<HTMLAnchorElement>("a[href^='#']")
        : null;
    if (
      !link ||
      event.ctrlKey ||
      event.metaKey ||
      event.shiftKey ||
      event.altKey
    )
      return;
    if (link.getAttribute("href") === "#main") {
      const main = document.querySelector<HTMLElement>("#main");
      if (!main) return;
      event.preventDefault();
      main.focus();
      return;
    }
    const index = sceneElements.findIndex(
      (scene) => `#${scene.id}` === link.getAttribute("href"),
    );
    if (index < 0) return;
    event.preventDefault();
    navigate(index, true);
  });
  window.addEventListener("hashchange", () => showScene(hashIndex()));
  window.addEventListener("popstate", () => showScene(hashIndex()));
  showScene(hashIndex());
  initializeTheme();
  initializeFullscreen();
  initializeCamera();
}
