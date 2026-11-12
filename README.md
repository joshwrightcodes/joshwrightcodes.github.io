# josh.wright.codes

This repository holds the source of my personal site, [josh.wright.codes](https://josh.wright.codes). The site is one static page with no build step. GitHub Pages serves it from the `main` branch.

## Preview the site

Run this command from the repository root, then open <http://localhost:8123>:

```sh
python3 -m http.server 8123
```

## Run the checks

The checks need Python 3 and no other tools:

```sh
python3 -m unittest discover -s tests -v
```

The file `tests/approved-copy.txt` holds the text that the page must contain. Change that file when you change the text of the page.

## Licence

The site is under the licence in [LICENSE](LICENSE). The Overpass font has its own licence in `assets/fonts/OFL.txt`.
