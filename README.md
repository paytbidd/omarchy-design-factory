# Omarchy plugins

Payton Biddington’s public shelf of [Omarchy](https://omarchy.org) tweaks.

**Live site:** [https://paytbidd.github.io/omarchy-plugins/](https://paytbidd.github.io/omarchy-plugins/)

GitHub Pages default URL only. No custom DNS. Nothing is submitted to a marketplace.

The header is Payton’s GitHub avatar, name, and [github.com/paytbidd](https://github.com/paytbidd). Listings are one full-width row each. Body type and surfaces are neutrals. **Blue** (light) and **orange** (dark) are accent only — links, icons, focus, copy/moon hover. A moon in the footer overrides `prefers-color-scheme` (filled = night, outline = day) and persists in `localStorage`.

## What ships

- Static site in `site/`
- 24×24 one-color marks from [pixelarticons](https://github.com/halfmage/pixelarticons) (MIT)
- Install line for every plugin:

  ```bash
  omarchy plugin add https://github.com/paytbidd/<repo>.git --enable
  ```

- A GitHub Action that lists public `paytbidd` repos prefixed `omarchy-*` and deploys Pages
- A reusable **Marketplace verify** workflow that plugin repos call after a real change, opening or updating a `[Verify]` issue on [omacom/omarchy-plugin-marketplace](https://github.com/omacom/omarchy-plugin-marketplace) when HEAD differs from the listed snapshot
- `omarchy-plugins` (this site) is excluded from the shelf

## Auto-list

[`.github/workflows/pages.yml`](.github/workflows/pages.yml) runs on every push to `main`, every six hours, and on demand.

[`scripts/list_plugins.py`](scripts/list_plugins.py) calls the public GitHub API, keeps `omarchy-*` repos, drops this site, and writes `site/data/plugins.json`. The site then merges that list with hand overrides.

Pages source is **GitHub Actions**. After a green **Deploy site** run the URL above is live.

## Hand overrides

Edit [`site/data/overrides.json`](site/data/overrides.json).

```json
{
  "exclude": ["omarchy-plugins"],
  "order": ["omarchy-patina", "omarchy-redlight", "omarchy-macromancy"],
  "plugins": {
    "omarchy-type": {
      "title": "Type",
      "blurb": "One-line description.",
      "icon": "icons/type.svg"
    }
  }
}
```

| Field | Effect |
| --- | --- |
| `exclude` | Extra repo names to hide (this repo is always hidden) |
| `order` | Repo names in display order. Named first, then the rest A–Z |
| `title` | Row heading. Default: `omarchy-` stripped and title-cased |
| `blurb` | One-line description. Default: the GitHub repo description |
| `icon` | Path under `site/` to a 1-color SVG. Default: `icons/<short-name>.svg`, then `icons/default.svg` |
| `hidden: true` | Keep the repo out of the list |

A new public `omarchy-*` repo on `paytbidd` shows up on the next Action run. Add an override if you want a tighter blurb or a custom mark.

## Marketplace verify

Listed `paytbidd/omarchy-*` plugins call [`.github/workflows/marketplace-verify.yml`](.github/workflows/marketplace-verify.yml) from their own `Marketplace verify` workflow. That runs on `workflow_dispatch` and on pushes to `main` that change plugin files (not `.github/`).

It files **Verify and publish a newer upstream commit** when the catalog SHA is behind HEAD, skips when they already match, and edits an open `[Verify]` issue instead of opening a duplicate. Maintainer `approved-and-verified` still has to happen on the marketplace side.

Each plugin repo needs a `MARKETPLACE_GH_TOKEN` secret that can open issues on `omacom/omarchy-plugin-marketplace` (a `gh` token with `repo` or a classic PAT with `public_repo`).

```bash
python3 scripts/marketplace_verify.py --root ../omarchy-weather --dry-run
```

## Icons

Plugin marks are vendored from **pixelarticons** (MIT, © Gerrit Halfmann), a strict 24×24 `currentColor` grid. Displayed at 24px so the pixels stay sharp.

| Plugin | Glyph |
| --- | --- |
| Apple Music Mini | `music` |
| Macromancy | `command` (⌘) |
| Patina | `frame` |
| Redlight | `sun` |
| Soundstage | `monitor` |
| Type | `letter-t` |
| Forecast | `cloud-sun` |
| Default | `layout` |
| Copy / copied | `copy` / `check` |

The 16px GitHub mark next to each repo name is from **Primer Octicons** (MIT, © GitHub). The footer moon is a 16px crescent: outline for day, filled for night.

See [`site/icons/LICENSE-pixelarticons.txt`](site/icons/LICENSE-pixelarticons.txt). Typeface is [Geist](https://vercel.com/font) (SIL OFL), the same family omarchy.org uses.

## Local

```bash
python3 scripts/list_plugins.py
python3 -m unittest scripts.test_list_plugins
python3 -m http.server 4173 --directory site
```

Then open http://127.0.0.1:4173/

## Owner

[Payton Biddington](https://github.com/paytbidd) · [paytonb.com](https://paytonb.com)
