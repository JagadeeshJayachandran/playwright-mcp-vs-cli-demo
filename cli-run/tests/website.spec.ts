import { test, expect, type Locator, type Page } from '@playwright/test';

const HOME_URL = 'https://jagadeeshjayachandran.dev/';

async function goToSection(page: Page, linkName: string, hash: string) {
  await page
    .getByRole('navigation', { name: 'Main navigation' })
    .getByRole('link', { name: linkName, exact: true })
    .click();
  await expect(page).toHaveURL(new RegExp(`#${hash}$`));
}

// Nav links smooth-scroll in JS, so a click straight after navigating can land
// mid-scroll and miss its target. Retry the click until its effect shows up.
async function clickUntil(target: Locator, effect: () => Promise<void>) {
  await expect(async () => {
    await target.click();
    await effect();
  }).toPass({ timeout: 10_000 });
}

// Read-only journey: the contact and waitlist forms are never filled or submitted,
// and the booking/waitlist links are never clicked.
test.describe('jagadeeshjayachandran.dev', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(HOME_URL);
  });

  test('home page journey', async ({ page }) => {
    // AI model cards load asynchronously and re-anchor the page to the current
    // #hash when they render; wait for them so that jump can't happen mid-journey.
    await expect(page.getByRole('heading', { level: 3, name: 'Coding', exact: true })).toBeAttached();

    await test.step('1. "Schedule a 1:1 chat" button is visible', async () => {
      await expect(page.getByRole('link', { name: 'Schedule a 1:1 chat', exact: true })).toBeVisible();
    });

    await test.step('2. Work nav link shows the My Work section', async () => {
      await goToSection(page, 'Work', 'work');
      await expect(page.getByRole('heading', { name: 'My Work' })).toBeInViewport();
    });

    const panel = page.getByRole('tabpanel');

    await test.step('3. QE Projects and Prompts & Custom GPTs tabs change the content', async () => {
      await expect(panel).toHaveAccessibleName('Automations & Tools');
      const automationsText = await panel.innerText();

      const qeProjects = page.getByRole('tab', { name: 'QE Projects' });
      await clickUntil(qeProjects, () =>
        expect(qeProjects).toHaveAttribute('aria-selected', 'true', { timeout: 1_000 }),
      );
      await expect(panel).toHaveAccessibleName('QE Projects');
      await expect(panel).not.toHaveText(automationsText);
      const qeProjectsText = await panel.innerText();

      const prompts = page.getByRole('tab', { name: 'Prompts & Custom GPTs' });
      await clickUntil(prompts, () =>
        expect(prompts).toHaveAttribute('aria-selected', 'true', { timeout: 1_000 }),
      );
      await expect(panel).toHaveAccessibleName('Prompts & Custom GPTs');
      await expect(panel).not.toHaveText(qeProjectsText);
      await expect(panel.getByRole('heading', { name: 'Interactive Prompt Library' })).toBeVisible();
    });

    await test.step('4. Selecting "Playwright Automation Framework Setup" shows a prompt', async () => {
      const prompt = panel.getByRole('code');
      await expect(prompt).toBeHidden();

      await panel
        .getByRole('combobox', { name: 'Choose a scenario:' })
        .selectOption('Playwright Automation Framework Setup');

      await expect(prompt).toBeVisible();
      await expect(prompt).toContainText('Playwright');
      await expect(panel.getByRole('button', { name: 'Copy' })).toBeVisible();
    });

    await test.step('5. Jargon search for "regression" shortens the list to matching terms', async () => {
      await goToSection(page, 'Jargon', 'jargon');
      await expect(page.getByRole('heading', { name: 'Industry Jargon' })).toBeInViewport();

      const terms = page.getByRole('button', { name: /flip for definition/ });
      const counter = page.getByText(/^\d+ of \d+ terms$/);
      const totalTerms = await terms.count();
      expect(totalTerms).toBeGreaterThan(1);
      await expect(counter).toHaveText(`${totalTerms} of ${totalTerms} terms`);

      await page.getByRole('textbox', { name: 'Search jargon terms' }).fill('regression');

      await expect.poll(() => terms.count()).toBeLessThan(totalTerms);
      await expect(page.getByRole('button', { name: /^Regression Suite/ })).toBeVisible();
      for (const term of await terms.all()) {
        await expect(term).toContainText(/regression/i);
      }
      await expect(counter).toHaveText(`${await terms.count()} of ${totalTerms} terms`);
    });

    await test.step('6. AI Models Coding and Research filters change the list', async () => {
      await goToSection(page, 'AI Models', 'ai-models');
      await expect(page.getByRole('heading', { name: 'AI Model Guide' })).toBeInViewport();

      const filters = page.getByRole('group', { name: 'Filter by workflow' });
      const codingList = page.getByRole('heading', { level: 3, name: 'Coding', exact: true });
      const researchList = page.getByRole('heading', { level: 3, name: 'Research', exact: true });
      await expect(codingList).toBeVisible();
      await expect(researchList).toBeVisible();

      await clickUntil(filters.getByRole('button', { name: 'Coding' }), () =>
        expect(researchList).toBeHidden({ timeout: 1_000 }),
      );
      await expect(codingList).toBeVisible();

      await clickUntil(filters.getByRole('button', { name: 'Research' }), () =>
        expect(codingList).toBeHidden({ timeout: 1_000 }),
      );
      await expect(researchList).toBeVisible();
    });

    await test.step('7. Contact form shows Name, Email, Role, Company and Message fields', async () => {
      await goToSection(page, 'Contact', 'contact');

      for (const field of ['Name', 'Email', 'Role', 'Company']) {
        const input = page.getByRole('textbox', { name: field, exact: true });
        await expect(input).toBeVisible();
        await expect(input).toHaveValue('');
      }

      // The Message field is labelled "How can I help?" on the page.
      const message = page.getByRole('textbox', { name: 'How can I help?' });
      await expect(message).toBeVisible();
      await expect(message).toHaveAttribute('name', 'message');
      await expect(message).toHaveValue('');

      await expect(page.getByRole('button', { name: 'Send Message' })).toBeVisible();
    });
  });

  test('cohort page', async ({ page }) => {
    await test.step('8. Cohort nav link opens the QE Architect Accelerator page', async () => {
      await page.getByRole('navigation', { name: 'Main navigation' }).getByRole('link', { name: 'Cohort' }).click();
      await expect(page).toHaveURL(/\/cohort\/?$/);
      await expect(page).toHaveTitle(/QE Architect Accelerator/);
    });

    await test.step('9. Key section headings are visible', async () => {
      for (const heading of ['Who this is for', 'How it works', 'Results from the first cohort']) {
        await expect(page.getByRole('heading', { name: heading })).toBeVisible();
      }
    });

    await test.step('10. Booking and waitlist buttons are visible (not clicked)', async () => {
      await expect(page.getByRole('link', { name: 'Book a 20-minute call' }).first()).toBeVisible();
      await expect(
        page
          .getByRole('link', { name: 'Join the waitlist' })
          .or(page.getByRole('button', { name: 'Join the waitlist' }))
          .first(),
      ).toBeVisible();
    });
  });
});
