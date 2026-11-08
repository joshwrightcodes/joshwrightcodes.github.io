"""Checks for the static site. Run with: python3 -m unittest discover -s tests -v"""
import pathlib
import re
import unittest
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
NO_TEXT_TAGS = {"script", "style", "title"}


class Page(HTMLParser):
    """Parsed index.html: elements with their ancestors, and visible text."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.elements = []
        self.stack = []
        self.text = []
        self.ids = {}
        self.headings = []

    def _hidden_text(self):
        return any(e["tag"] in NO_TEXT_TAGS or e["attrs"].get("id") == "theme-toggle" for e in self.stack)

    def handle_starttag(self, tag, attrs):
        element = {"tag": tag, "attrs": dict(attrs), "ancestors": list(self.stack), "text": ""}
        self.elements.append(element)
        if "id" in element["attrs"]:
            self.ids[element["attrs"]["id"]] = len("".join(self.text))
        if tag not in VOID_TAGS:
            self.stack.append(element)
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.headings.append(element)

    def handle_endtag(self, tag):
        while self.stack:
            if self.stack.pop()["tag"] == tag:
                break

    def handle_data(self, data):
        for element in self.stack:
            element["text"] += data
        if not self._hidden_text():
            self.text.append(data)

    def find(self, tag):
        return [e for e in self.elements if e["tag"] == tag]

    def inside(self, tag, css_class):
        def has_class(element):
            return css_class in element["attrs"].get("class", "").split()

        return [e for e in self.find(tag) if any(has_class(a) for a in e["ancestors"])]


def page():
    parsed = Page()
    parsed.feed((ROOT / "index.html").read_text())
    return parsed


def normalise(text):
    return " ".join(text.split())


def visible_text(parsed=None):
    parsed = parsed or page()
    return normalise("".join(parsed.text))


class ContentTests(unittest.TestCase):
    def test_approved_copy_present(self):
        text = visible_text()
        missing = [
            line
            for line in (ROOT / "tests/approved-copy.txt").read_text().splitlines()
            if line.strip() and normalise(line) not in text
        ]
        self.assertEqual(missing, [])

    def test_single_h1(self):
        headings = page().find("h1")
        self.assertEqual(len(headings), 1)
        self.assertEqual(normalise(headings[0]["text"]), "I build the systems other engineers ship through.")

    def test_heading_levels_do_not_skip(self):
        levels = [int(h["tag"][1]) for h in page().headings]
        self.assertEqual(levels[0], 1)
        for previous, current in zip(levels, levels[1:]):
            self.assertLessEqual(current, previous + 1, f"{previous} then {current}")

    def test_in_page_links_resolve(self):
        parsed = page()
        anchors = [a["attrs"]["href"][1:] for a in parsed.find("a") if a["attrs"].get("href", "").startswith("#")]
        self.assertTrue(anchors)
        self.assertEqual([a for a in anchors if a not in parsed.ids], [])

    def test_required_links(self):
        hrefs = {a["attrs"].get("href") for a in page().find("a")}
        for target in (
            "https://github.com/joshwrightcodes",
            "https://www.linkedin.com/in/joshwrightau",
            "mailto:josh@wright.codes",
            "https://github.com/joshwrightcodes/bk-agent-stack-orchard",
            "https://github.com/joshwrightcodes/bk-agent-stack-orchard/blob/main/docs/adrs/README.md",
        ):
            self.assertIn(target, hrefs)

    def test_stations_link_to_entries(self):
        hrefs = [a["attrs"]["href"] for a in page().inside("a", "route")]
        self.assertEqual(hrefs, ["#create", "#build", "#ship", "#run", "#observe"])

    def test_former_name_only_in_career(self):
        parsed = page()
        before_career = "".join(parsed.text)[: parsed.ids["career"]]
        self.assertNotIn("SafetyCulture", before_career)

    def test_jekyll_files_removed(self):
        for name in ("_config.yml", "Gemfile", "index.md", "assets/main.scss"):
            self.assertFalse((ROOT / name).exists(), name)
        self.assertTrue((ROOT / ".nojekyll").exists())

    def test_cname_unchanged(self):
        self.assertEqual((ROOT / "CNAME").read_text().strip(), "josh.wright.codes")


PALETTES = {
    "light": ("#F1F6F8", "#12263A", "#41566A", "#0B5CAD", "#B26A00", "#FFFFFF"),
    "dark": ("#10222E", "#E8F0F4", "#AFC2CE", "#6CB2F2", "#F4B13D", "#10222E"),
    "light-hc": ("#FFFFFF", "#000000", "#24343F", "#00408F", "#7A4300", "#FFFFFF"),
    "dark-hc": ("#000000", "#FFFFFF", "#E3EBF0", "#9AD0FF", "#FFC95C", "#000000"),
}
TOKENS = ("bg", "ink", "muted", "line", "branch", "station")


def stylesheet():
    return (ROOT / "assets/site.css").read_text()


def token_blocks():
    """Return one tuple of token values for each CSS rule that sets --bg."""
    blocks = []
    for body in re.findall(r"\{([^{}]*--bg:[^{}]*)\}", stylesheet()):
        values = dict(re.findall(r"--([a-z]+):\s*(#[0-9A-Fa-f]{6})", body))
        blocks.append(tuple(values.get(token, "") for token in TOKENS))
    return blocks


def luminance(colour):
    channels = [int(colour[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(first, second):
    lighter, darker = sorted((luminance(first), luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


class ThemeTests(unittest.TestCase):
    def test_every_token_block_is_a_known_palette(self):
        known = set(PALETTES.values())
        self.assertEqual([b for b in token_blocks() if b not in known], [])

    def test_all_four_palettes_exist(self):
        self.assertEqual(set(token_blocks()), set(PALETTES.values()))

    def test_contrast_targets(self):
        for name, (bg, ink, muted, line, branch, _station) in PALETTES.items():
            with self.subTest(name):
                self.assertGreaterEqual(contrast(ink, bg), 7)
                self.assertGreaterEqual(contrast(muted, bg), 7 if name.endswith("-hc") else 4.5)
                self.assertGreaterEqual(contrast(line, bg), 3)
                self.assertGreaterEqual(contrast(branch, bg), 3)


class RequestTests(unittest.TestCase):
    def test_no_third_party_requests(self):
        parsed = page()
        external = re.compile(r"^(https?:)?//")
        requested = [
            e["attrs"].get("href") or e["attrs"].get("src") or ""
            for e in parsed.elements
            if (e["tag"] == "link" and e["attrs"].get("rel") != "canonical") or e["tag"] in {"script", "img"}
        ]
        self.assertEqual([url for url in requested if external.match(url)], [])
        self.assertNotIn("@import", stylesheet())
        self.assertEqual(re.findall(r"url\(\s*['\"]?(?:https?:)?//[^)]*\)", stylesheet()), [])

    def test_fonts_are_woff2(self):
        fonts = list((ROOT / "assets/fonts").glob("*.woff2"))
        self.assertTrue(fonts)
        for font in fonts:
            self.assertEqual(font.read_bytes()[:4], b"wOF2", font.name)


class ToggleTests(unittest.TestCase):
    def theme_script(self):
        parsed = page()
        scripts = [e for e in parsed.find("script") if e["attrs"].get("src") == "assets/theme.js"]
        self.assertEqual(len(scripts), 1)
        return scripts[0]

    def test_theme_script_loads_blocking_in_head(self):
        script = self.theme_script()
        self.assertIn("head", [a["tag"] for a in script["ancestors"]])
        self.assertNotIn("defer", script["attrs"])
        self.assertNotIn("async", script["attrs"])

    def test_toggle_hidden_without_javascript(self):
        buttons = [e for e in page().find("button") if e["attrs"].get("id") == "theme-toggle"]
        self.assertEqual(len(buttons), 1)
        self.assertIn("hidden", buttons[0]["attrs"])
        self.assertEqual(buttons[0]["attrs"].get("aria-pressed"), "false")

    def test_page_has_no_other_scripts(self):
        scripts = [e for e in page().find("script") if e["attrs"].get("type") != "application/ld+json"]
        self.assertEqual([e["attrs"].get("src") for e in scripts], ["assets/theme.js"])
        self.assertEqual(normalise(scripts[0]["text"]), "")


if __name__ == "__main__":
    unittest.main()
