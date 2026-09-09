import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const route = "./presentation/";
const scenes = [
  "a-engenharia-permanece",
  "contexto",
  "convergencia",
  "conhecimento",
  "coordenacao",
  "governanca",
  "portabilidade",
  "arquitetura",
  "adapters",
  "fluxo",
  "o-que-permanece",
] as const;

test("scene navigation supports retakes, history, bounds, and native controls", async ({
  page,
}) => {
  await page.goto(route);
  await expect(page.locator("[data-scene]:visible")).toHaveCount(1);
  await expect(
    page.getByRole("button", { name: "Cena anterior", exact: true }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Próxima cena", exact: true }).click();
  await expect(page).toHaveURL(/#contexto$/);
  await page.keyboard.press("ArrowRight");
  await expect(page).toHaveURL(/#convergencia$/);
  await page.goBack();
  await expect(page.locator("#contexto")).toBeVisible();
  await page.goForward();
  await expect(page.locator("#convergencia")).toBeVisible();
  await page.reload();
  await expect(page.locator("#convergencia")).toBeVisible();
  await page.getByRole("button", { name: "Alternar tema" }).focus();
  await page.keyboard.press("ArrowLeft");
  await expect(page).toHaveURL(/#convergencia$/);
  const selector = page.getByRole("combobox", { name: "Ir para cena" });
  await selector.selectOption("governanca");
  await expect(page.locator("#governanca")).toBeVisible();
  await page.locator("#governanca h2").focus();
  await page.keyboard.press("End");
  await expect(page.locator("#o-que-permanece")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Próxima cena", exact: true }),
  ).toBeDisabled();
  await page.keyboard.press("Home");
  await expect(page.locator("#a-engenharia-permanece")).toBeVisible();
});

test("skip link focuses content without changing the active scene", async ({
  page,
}) => {
  await page.goto(`${route}#governanca`);
  await page.getByRole("link", { name: "Pular para o conteúdo" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("#main")).toBeFocused();
  await expect(page).toHaveURL(/#governanca$/);
  await expect(page.locator("#governanca")).toBeVisible();
  await expect(page.locator("[data-scene]:visible")).toHaveCount(1);
});

test("invalid scene fragments recover to the opening", async ({ page }) => {
  await page.goto(`${route}#unknown-scene`);
  await expect(page.locator("#a-engenharia-permanece")).toBeVisible();
  await expect(page.locator("[data-scene]:visible")).toHaveCount(1);
});

test("theme choice persists and enlarged text remains readable", async ({
  page,
}) => {
  await page.emulateMedia({ colorScheme: "light", reducedMotion: "reduce" });
  await page.goto(route);
  await page.getByRole("button", { name: "Alternar tema" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.setViewportSize({ width: 640, height: 720 });
  await page.addStyleTag({ content: "html { font-size: 200%; }" });
  for (const scene of [
    "conhecimento",
    "governanca",
    "arquitetura",
    "adapters",
  ]) {
    await page
      .getByRole("combobox", { name: "Ir para cena" })
      .selectOption(scene);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  }
});

test("coordination scene stays aligned and clear of the controls", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto(`${route}#coordenacao`);

  const labelsPrecedeBars = await page
    .locator("#coordenacao .work-lanes > div")
    .evaluateAll((lanes) =>
      lanes.every((lane) => {
        const label = lane.querySelector("strong");
        const bars = [...lane.querySelectorAll("i")];
        if (!label || bars.length === 0) return false;

        const labelRight = label.getBoundingClientRect().right;
        return bars.every(
          (bar) => bar.getBoundingClientRect().left > labelRight,
        );
      }),
    );

  expect(labelsPrecedeBars).toBe(true);

  const footnoteClearsControls = await page
    .locator("#coordenacao .scene-footnote")
    .evaluate((footnote) => {
      const controls = document.querySelector(".narrative-controls");
      if (!controls) return false;

      return (
        footnote.getBoundingClientRect().bottom <=
        controls.getBoundingClientRect().top
      );
    });

  expect(footnoteClearsControls).toBe(true);
});

for (const viewport of [
  { width: 390, height: 844 },
  { width: 1280, height: 720 },
  { width: 1920, height: 1080 },
]) {
  test(`all scenes reflow at ${viewport.width}×${viewport.height}`, async ({
    page,
  }) => {
    await page.setViewportSize(viewport);
    const failures: string[] = [];
    page.on("pageerror", (error) => failures.push(error.message));
    await page.goto(route);
    for (const scene of scenes) {
      await page
        .getByRole("combobox", { name: "Ir para cena" })
        .selectOption(scene);
      await expect(page.locator(`#${scene}`)).toBeVisible();
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
    }
    await page
      .getByRole("button", { name: "Reservar espaço para câmera" })
      .click();
    await expect(
      page.getByRole("button", { name: "Reservar espaço para câmera" }),
    ).toHaveAttribute("aria-pressed", "true");
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect(failures).toEqual([]);
  });
}

test("all scenes pass automated contrast and semantic checks in both themes", async ({
  page,
}) => {
  test.setTimeout(90_000);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto(route);
  for (const theme of ["light", "dark"]) {
    await page.evaluate((value) => {
      localStorage.setItem("omh-theme", value);
      document.documentElement.dataset.theme = value;
    }, theme);
    for (const scene of scenes) {
      await page
        .getByRole("combobox", { name: "Ir para cena" })
        .selectOption(scene);
      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze();
      expect.soft(results.violations, `${theme}: ${scene}`).toEqual([]);
    }
  }
});

test("all eleven scenes remain readable without JavaScript", async ({
  browser,
  baseURL,
}) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto(new URL("presentation/", baseURL).href);
  await expect(page.locator("[data-scene]:visible")).toHaveCount(11);
  await expect(
    page.getByRole("button", { name: "Próxima cena", exact: true }),
  ).toBeHidden();
  await context.close();
});
