import csv, json, os, tempfile, unittest
from pathlib import Path

from rift_core import compare_trees, export_csv, export_json, scan_tree, summarize


class RiftBehaviourTests(unittest.TestCase):
    def setUp(self):
        self._a = tempfile.TemporaryDirectory(); self._b = tempfile.TemporaryDirectory()
        self.left, self.right = Path(self._a.name), Path(self._b.name)
    def tearDown(self):
        self._a.cleanup(); self._b.cleanup()

    def put(self, root, rel, text, mtime=None):
        p = root / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)
        if mtime is not None: os.utime(p, (mtime, mtime))
        return p

    def statuses(self, hash_files=True, **kw):
        entries = compare_trees(scan_tree(self.left, hash_files=hash_files), scan_tree(self.right, hash_files=hash_files), **kw)
        return {(e.status, e.relpath, e.renamed_from) for e in entries}

    def test_identical_trees_are_all_unchanged(self):
        for root in (self.left, self.right): self.put(root, 'a/b.txt', 'same', 1_000_000)
        self.assertEqual(self.statuses(), {('unchanged', 'a/b.txt', None)})

    def test_empty_trees_compare_to_nothing(self):
        self.assertEqual(summarize(compare_trees({}, {})), {'added': 0, 'removed': 0, 'modified': 0, 'renamed': 0, 'unchanged': 0})

    def test_hashing_ignores_touched_but_identical_files(self):
        self.put(self.left, 'f.txt', 'same', 1_000_000); self.put(self.right, 'f.txt', 'same', 2_000_000)
        self.assertEqual(self.statuses(hash_files=True), {('unchanged', 'f.txt', None)})
        self.assertEqual(self.statuses(hash_files=False), {('modified', 'f.txt', None)})

    def test_same_size_different_content_is_modified_when_hashing(self):
        self.put(self.left, 'f.txt', 'aaaa', 1_000_000); self.put(self.right, 'f.txt', 'bbbb', 1_000_000)
        self.assertEqual(self.statuses(), {('modified', 'f.txt', None)})

    def test_rename_detection_can_be_turned_off(self):
        self.put(self.left, 'old.txt', 'content'); self.put(self.right, 'new.txt', 'content')
        self.assertEqual(self.statuses(detect_renames=False), {('removed', 'old.txt', None), ('added', 'new.txt', None)})

    def test_each_target_is_claimed_by_only_one_rename(self):
        self.put(self.left, 'one.txt', 'twin'); self.put(self.left, 'two.txt', 'twin'); self.put(self.right, 'moved.txt', 'twin')
        result = self.statuses()
        self.assertEqual(len([s for s in result if s[0] == 'renamed']), 1)
        self.assertEqual(len([s for s in result if s[0] == 'removed']), 1)

    def test_ignored_directories_are_skipped_and_paths_use_forward_slashes(self):
        self.put(self.left, '.git/HEAD', 'ref'); self.put(self.left, 'node_modules/x/index.js', 'x'); self.put(self.left, 'src/deep/mod.py', 'm')
        self.assertEqual(set(scan_tree(self.left)), {'src/deep/mod.py'})

    def test_exports_round_trip(self):
        self.put(self.left, 'gone.txt', 'g'); self.put(self.right, 'new.txt', 'n')
        entries = compare_trees(scan_tree(self.left, hash_files=True), scan_tree(self.right, hash_files=True))
        with tempfile.TemporaryDirectory() as out:
            export_json(entries, Path(out) / 'd.json'); export_csv(entries, Path(out) / 'd.csv')
            data = json.loads((Path(out) / 'd.json').read_text())
            rows = list(csv.DictReader((Path(out) / 'd.csv').open()))
        self.assertEqual({d['status'] for d in data}, {'added', 'removed'})
        self.assertEqual({r['path'] for r in rows}, {'gone.txt', 'new.txt'})


if __name__ == '__main__':
    unittest.main()
