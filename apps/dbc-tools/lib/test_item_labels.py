"""lib/item_labels.py: the client tier label table (item-variants IV4)."""

import tempfile
import unittest
from pathlib import Path

from lib import item_labels


class RenderTest(unittest.TestCase):
    def test_sorted_deterministic_lf(self):
        text = item_labels.render_lua({71002: "Molten Empowered", 5187: "Normal", 71001: "Normal"})
        self.assertEqual(text, item_labels.render_lua({5187: "Normal", 71001: "Normal", 71002: "Molten Empowered"}))
        body = text.split("ITEM_TIER_LABELS = {\n")[1]
        want = '    [5187] = "Normal",\n    [71001] = "Normal",\n    [71002] = "Molten Empowered",\n}\n'
        self.assertEqual(body, want)
        self.assertNotIn("\r", text)
        self.assertTrue(all(len(line) <= 120 for line in text.splitlines()))

    def test_empty_table(self):
        self.assertTrue(item_labels.render_lua({}).endswith("ITEM_TIER_LABELS = {\n}\n"))

    def test_bad_labels_rejected(self):
        for bad in ("", " Normal", 'Say "hi"', "a|cffff0000b", "back\\slash", "two\nlines", "tab\tbed"):
            with self.assertRaises(ValueError, msg=repr(bad)):
                item_labels.render_lua({1: bad})
        with self.assertRaises(ValueError):
            item_labels.render_lua({0: "Normal"})
        text, errors = item_labels.prepare({1: "a|b"})
        self.assertIsNone(text)
        self.assertEqual(len(errors), 1)


class WriteTest(unittest.TestCase):
    def test_write_only_when_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Interface" / "FrameXML" / "ItemTierLabels.lua"
            text = item_labels.render_lua({5187: "Normal"})
            self.assertTrue(item_labels.is_stale(text, path))
            self.assertTrue(item_labels.write(text, path))
            self.assertFalse(item_labels.write(text, path))
            self.assertIsNone(item_labels.finish(text, check=True, path=path))
            other = item_labels.render_lua({5187: "Normal", 5188: "Normal"})
            self.assertIn("stale", item_labels.finish(other, check=True, path=path))
            self.assertEqual(path.read_text(encoding="utf-8"), text)  # a check never writes
            self.assertIn("wrote", item_labels.finish(other, path=path))
            self.assertIsNone(item_labels.finish(other, path=path))


if __name__ == "__main__":
    unittest.main()
