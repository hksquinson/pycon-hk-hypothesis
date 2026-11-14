# Slides

The deck uses [Marp](https://marp.app/): a single Markdown file rendered to HTML/PDF.

## Commands

```bash
npm install
npm run slides:build   # HTML -> slides/dist/talk.html
npm run slides:pdf     # PDF -> slides/dist/talk.pdf (requires Chrome/Chromium)
npm run slides:watch   # live preview
```

If Chrome/Chromium is not on your `PATH`, install one with Puppeteer and point
Marp at it:

```bash
npx --yes puppeteer browsers install chrome
CHROME_PATH="$(find "$HOME/.cache/puppeteer/chrome" -name chrome -type f | head -n 1)" \
  npm run slides:pdf
```

`slides/dist/` is tracked so the built HTML and PDF are available without a
build. `node_modules/` is gitignored.

## Why Marp

- Markdown source, so the deck lives next to the code and diffs cleanly.
- Built-in code highlighting, speaker notes, and PDF/HTML export.
- No app runtime or Vue components needed for a 30-minute talk with static code slides.

Slidev is the alternative if we later want Vue components, animations, or a more app-like deck.
