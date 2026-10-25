# Playwright MCP vs Playwright CLI

The same 10-step browser test journey, given to an AI coding agent (Claude Code) two ways:

- **`mcp-run/`**: the agent drives the browser through the [Playwright MCP server](https://github.com/microsoft/playwright-mcp).
- **`cli-run/`**: the agent drives the browser by running [Playwright CLI](https://www.npmjs.com/package/@playwright/cli) shell commands.

Both runs test the live site https://jagadeeshjayachandran.dev. The two prompts are identical apart from the first line, which names the tool to use.

## What's in the repo

```
MCP Prompt.txt        Journey prompt for the MCP run
CLI prompts.txt       Journey prompt for the CLI run
convert_Test.txt      Follow-up prompt: turn the journey into a Playwright test

mcp-run/
  .playwright-mcp/    Page snapshots the MCP server saved during the run
  tests/              Playwright's sample test (example.spec.ts)

cli-run/
  .claude/skills/     The playwright-cli skill Claude Code uses to learn the commands
  .playwright-cli/    Page snapshots the CLI saved during the run
  tests/
    website.spec.ts   The test generated from the CLI journey
    example.spec.ts   Playwright's sample test
```

The snapshot folders hold YAML accessibility snapshots of the page, one per step the agent took. Compare them to see what each approach "saw" while it worked.

## The journey

Home page: check the "Schedule a 1:1 chat" button, then the Work, Jargon, AI Models and Contact sections. Cohort page: check the page title, the key headings, and the booking and waitlist buttons.

The journey is **read-only**. It never fills in or submits a form, and never clicks the booking or waitlist buttons. Keep it that way if you adapt it: it runs against a real site.

## Run the generated test

You need Node.js (LTS).

```bash
cd cli-run
npm install
npx playwright install
npx playwright test tests/website.spec.ts
npx playwright show-report
```

The config runs every test in Chromium, Firefox and WebKit. Because it tests a live site, the test can fail when the site's content changes.

## Reproduce the comparison yourself

You need Node.js and [Claude Code](https://docs.claude.com/en/docs/claude-code/overview).

**MCP run**

```bash
cd mcp-run
npm install
claude mcp add playwright npx @playwright/mcp@latest
claude
```

Paste the contents of `MCP Prompt.txt`. When the journey finishes, paste `convert_Test.txt`.

**CLI run**

```bash
npm install -g @playwright/cli
cd cli-run
npm install
claude
```

The `playwright-cli` skill is already in `cli-run/.claude/skills/`, so Claude Code picks it up automatically. Paste the contents of `CLI prompts.txt`, then `convert_Test.txt`.

To test your own site, change the URL and the steps in the prompts.
