# Design Factory

Payton Biddington’s public shelf of [Omarchy](https://omarchy.org) plugins.

**Live site:** [https://paytbidd.github.io/omarchy-design-factory/](https://paytbidd.github.io/omarchy-design-factory/)

GitHub Pages default URL only. No custom DNS. Nothing is submitted to a marketplace.

The header is Payton’s GitHub avatar, name, [github.com/paytbidd](https://github.com/paytbidd), and a short factory blurb. Cards use `prefers-color-scheme`: **blue** in light, **orange** in dark.

## What ships

- Static site in `site/`
- One-color pixel SVG icons
- Install line for every plugin:

  ```bash
  omarchy plugin add https://github.com/paytbidd/<repo>.git --enable
  ```

- A GitHub Action that lists public `paytbidd` repos prefixed `omarchy-*` and deploys Pages
- `omarchy-design-factory` is excluded from the shelf

## Auto-list

[`.github/workflows/pages.yml`](.github/workflows/pages.yml) runs on every push to `main`, every six hours, and on demand.

[`scripts/list_plugins.py`](scripts/list_plugins.py) calls the public GitHub API, keeps `omarchy-*` repos, drops this site, and writes `site/data/plugins.json`. The site then merges that list with hand overrides.

Enable Pages once (this repo’s tokens cannot flip that setting):

1. Open [Settings → Pages](https://github.com/paytbidd/omarchy-design-factory/settings/pages)
2. Set **Source** to **GitHub Actions**
3. Re-run the **Deploy site** workflow under Actions

The first deploys failed with `Resource not accessible by integration` until that source is set. After a green deploy the URL above is live.

## Hand overrides

Edit [`site/data/overrides.json`](site/data/overrides.json).

```json
{
  "exclude": ["omarchy-design-factory"],
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
| `title` | Card heading. Default: `omarchy-` stripped and title-cased |
| `blurb` | One-line description. Default: the GitHub repo description |
| `icon` | Path under `site/` to a 1-color SVG. Default: `icons/<short-name>.svg`, then `icons/default.svg` |
| `hidden: true` | Keep the repo out of the grid |

Icons are 16×16 pixel SVGs filled with `currentColor`, so they follow the blue/orange accent. To add or redraw one, edit the ASCII maps in [`scripts/generate_icons.py`](scripts/generate_icons.py) and run:

```bash
python3 scripts/generate_icons.py
```

A new public `omarchy-*` repo on `paytbidd` shows up on the next Action run. Add an override if you want a tighter blurb or a custom mark.

## Local

```bash
python3 scripts/generate_icons.py
python3 scripts/list_plugins.py
python3 -m unittest scripts/test_list_plugins.py
python3 -m http.server 4173 --directory site
```

Then open http://127.0.0.1:4173/

## Owner

[Payton Biddington](https://github.com/paytbidd) · [paytonb.com](https://paytonb.com)
