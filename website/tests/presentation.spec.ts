import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("reader and presentation pass automated accessibility checks", async ({
  page,
}) => {
  await page.goto("./");
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.goto("./?present=1#knowledge");
  await page.getByRole("button", { name: "Revelar diagrama" }).click();
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
});

test("enlarged text reflows without horizontal page overflow", async ({
  page,
}) => {
  await page.setViewportSize({ width: 640, height: 720 });
  await page.goto("./");
  await page.addStyleTag({ content: "html { font-size: 200%; }" });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});

test("reader exposes the complete guide and local assets", async ({ page }) => {
  const failures: string[] = [];
  page.on("pageerror", (error) => failures.push(error.message));
  page.on("response", (response) => {
    if (response.status() >= 400) failures.push(response.url());
  });
  await page.goto("./");
  await expect(page.locator("html")).toHaveAttribute("lang", "pt-BR");
  await expect(page.locator("[data-chapter]:visible")).toHaveCount(8);
  await expect(page.locator(".deep-dive[open]")).toHaveCount(8);
  await expect(
    page.getByRole("navigation", { name: "Capítulos" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "04 Conhecimento" }).click();
  await expect(page).toHaveURL(/#knowledge$/);
  expect(failures).toEqual([]);
});

test("presentation supports reveal, navigation, retakes, notes and exit", async ({
  page,
}) => {
  await page.goto("./");
  await page.getByRole("button", { name: "Apresentar" }).click();
  await expect(page.locator("[data-chapter]:visible")).toHaveCount(1);
  await expect(page.locator("#origin .diagram")).toBeHidden();
  await page.getByRole("button", { name: "Revelar diagrama" }).click();
  await expect(page.locator("#origin .diagram")).toBeVisible();
  await page.getByRole("button", { name: "Próximo capítulo" }).click();
  await expect(page).toHaveURL(/present=1#architecture$/);
  await expect(page.locator("#architecture-title")).toBeFocused();
  await page.keyboard.press("ArrowRight");
  await expect(page).toHaveURL(/#evidence$/);
  await page.keyboard.press("ArrowLeft");
  await expect(page).toHaveURL(/#architecture$/);
  await page.getByRole("button", { name: "Notas", exact: true }).click();
  await expect(page.locator("#architecture .speaker-note")).toBeVisible();
  await page.getByRole("button", { name: "Área da câmera" }).click();
  await expect(page.locator("#camera-guide")).toBeVisible();
  await page.reload();
  await expect(page.locator("#architecture")).toBeVisible();
  await expect(page.locator("[data-chapter]:visible")).toHaveCount(1);
  await page.keyboard.press("Escape");
  await expect(page.locator("[data-chapter]:visible")).toHaveCount(8);
  await expect(page.locator(".deep-dive[open]")).toHaveCount(8);
  await expect(page.getByRole("button", { name: "Apresentar" })).toBeFocused();
});

test("native details keep their keyboard behavior", async ({ page }) => {
  await page.goto("./?present=1#knowledge");
  const summary = page.locator("#knowledge summary");
  await summary.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("#knowledge details")).toHaveAttribute("open", "");
  await page.keyboard.press("ArrowRight");
  await expect(page).toHaveURL(/#knowledge$/);
  await page.keyboard.press("Escape");
  await expect(page.locator("#presentation-controls")).toBeHidden();
});

test("browser history restores presentation mode without adding history entries", async ({
  page,
}) => {
  await page.goto("./?present=1#origin");
  await page.getByRole("button", { name: "Próximo capítulo" }).click();
  await page.keyboard.press("Escape");
  await expect(page.locator("[data-chapter]:visible")).toHaveCount(8);
  const length = await page.evaluate(() => history.length);
  await page.goBack();
  await expect(page).toHaveURL(/present=1#origin$/);
  await expect(page.locator("[data-chapter]:visible")).toHaveCount(1);
  await expect(page.locator("#presentation-controls")).toBeVisible();
  await page.goForward();
  await expect(page).toHaveURL(/\/#architecture$/);
  await expect(page.locator("[data-chapter]:visible")).toHaveCount(8);
  expect(await page.evaluate(() => history.length)).toBe(length);
});

for (const viewport of [
  { width: 390, height: 844 },
  { width: 1280, height: 720 },
  { width: 1920, height: 1080 },
]) {
  test(`layout fits ${viewport.width} by ${viewport.height}`, async ({
    page,
  }) => {
    await page.setViewportSize(viewport);
    await page.goto("./");
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await page.goto("./?present=1#knowledge");
    await page.getByRole("button", { name: "Revelar diagrama" }).click();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await page.getByRole("button", { name: "Área da câmera" }).click();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    if (viewport.width >= 900) {
      const diagram = await page.locator("#knowledge .diagram").boundingBox();
      const controls = await page
        .locator("#presentation-controls")
        .boundingBox();
      const guide = await page.locator("#camera-guide").boundingBox();
      expect(diagram).not.toBeNull();
      expect(controls).not.toBeNull();
      expect(guide).not.toBeNull();
      if (!diagram || !controls || !guide)
        throw new Error("Missing presentation geometry");
      expect(diagram.y + diagram.height).toBeLessThanOrEqual(controls.y);
      expect(diagram.x + diagram.width).toBeLessThanOrEqual(guide.x);
    }
  });
}

test("guide remains readable without JavaScript", async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:4321/oh-my-harness/");
  await expect(page.locator("[data-chapter]:visible")).toHaveCount(8);
  await expect(page.locator(".deep-dive[open]")).toHaveCount(8);
  await expect(page.getByRole("button", { name: "Apresentar" })).toBeHidden();
  await context.close();
});
