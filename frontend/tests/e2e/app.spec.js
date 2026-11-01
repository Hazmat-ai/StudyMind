import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
const content =
  "Relational databases organize data into tables. Primary keys identify rows and foreign keys express references. Normalization reduces redundancy.";
async function account(page) {
  const email = `student-${crypto.randomUUID()}@example.com`;
  await page.goto("/auth/register");
  await page.getByLabel("Email address").fill(email);
  await page
    .getByLabel("Password", { exact: true })
    .fill("a strong test passphrase");
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("Account created");
  await page.getByRole("link", { name: "Sign in", exact: true }).last().click();
  // The registration and login screens share field labels. Wait for the new
  // route and component before filling so a remount cannot erase the email.
  await expect(page).toHaveURL("/auth");
  await expect(
    page.getByRole("heading", { name: "Welcome back", exact: true }),
  ).toBeVisible();
  await page.getByLabel("Email address").fill(email);
  await expect(page.getByLabel("Email address")).toHaveValue(email);
  await page
    .getByLabel("Password", { exact: true })
    .fill("a strong test passphrase");
  const loginResponse = page.waitForResponse(
    (response) =>
      new URL(response.url()).pathname === "/api/auth/login" &&
      response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  const response = await loginResponse;
  expect(response.status(), "Sign-in API response").toBe(200);
  expect((await response.json()).user.email).toBe(email);
  await expect(page).toHaveURL("/");
  await expect(
    page.getByRole("link", { name: "Account", exact: true }),
  ).toBeVisible();
}
async function generate(page) {
  await page.getByLabel("Your notes", { exact: true }).fill(content);
  await expect(
    page.getByRole("button", { name: "Generate study set", exact: true }),
  ).toBeDisabled();
  await page.getByRole("checkbox", { name: /I agree to send/ }).check();
  await page
    .getByRole("button", { name: "Generate study set", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Relational databases", exact: true }),
  ).toBeVisible();
}
test("account, explicit consent, generation, recall, save, reload and deletion", async ({
  page,
}) => {
  await account(page);
  await generate(page);
  await page.getByRole("tab", { name: "Flashcards", exact: true }).click();
  await expect(page).toHaveURL(/tab=flashcards/);
  await page.getByRole("button", { name: /Key 1/ }).click();
  await expect(
    page.getByRole("button", { name: /A key identifies/ }),
  ).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("tab", { name: "Practice", exact: true }).click();
  await page
    .getByRole("button", { name: "Reveal answer", exact: true })
    .first()
    .click();
  await expect(page.getByText("Suggested answer").first()).toBeVisible();
  await page
    .getByRole("button", { name: "Save study set", exact: true })
    .click();
  await expect(page).not.toHaveURL(/draft-/);
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Relational databases", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Saved sets", exact: true })
    .first()
    .click();
  await expect(
    page.getByRole("link", { name: /Relational databases/ }),
  ).toBeVisible();
  page.on("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: /Delete/ }).click();
  await expect(
    page.getByRole("link", { name: /Relational databases/ }),
  ).toHaveCount(0);
});
test("learner screens and keyboard tabs have no serious automated accessibility violations", async ({
  page,
}) => {
  await account(page);
  await generate(page);
  for (const tab of ["Summary", "Flashcards", "Practice", "Concepts"]) {
    await page.getByRole("tab", { name: tab, exact: true }).click();
    const results = await new AxeBuilder({ page }).analyze();
    expect(
      results.violations.filter((v) =>
        ["serious", "critical"].includes(v.impact),
      ),
    ).toEqual([]);
  }
  await page.getByRole("tab", { name: "Concepts", exact: true }).press("Home");
  await expect(
    page.getByRole("tab", { name: "Summary", exact: true }),
  ).toBeFocused();
  for (const path of ["/", "/dashboard", "/account", "/privacy"]) {
    await page.goto(path);
    await expect(page.locator("main h1")).toBeVisible();
    const results = await new AxeBuilder({ page }).analyze();
    expect(
      results.violations.filter((v) =>
        ["serious", "critical"].includes(v.impact),
      ),
    ).toEqual([]);
  }
});
test("missing sets show an honest error and protected pages require sign-in", async ({
  page,
}) => {
  await page.goto("/dashboard");
  await expect(
    page.getByRole("heading", { name: "Welcome back" }),
  ).toBeVisible();
  await account(page);
  await page.goto("/results/00000000-0000-0000-0000-000000000000");
  await expect(page.getByRole("alert")).toContainText("not found");
  await expect(
    page.getByRole("heading", { name: "Relational databases", exact: true }),
  ).toHaveCount(0);
});
