"""Checks for the static site. Run with: python3 -m unittest discover -s tests -v"""
import pathlib
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


if __name__ == "__main__":
    unittest.main()
