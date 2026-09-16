import tempfile, unittest
from pathlib import Path
from rift_core import scan_tree, compare_trees, summarize

class RiftTests(unittest.TestCase):
    def test_added_removed_modified_and_renamed(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            pa,pb=Path(a),Path(b)
            (pa/'same.txt').write_text('same'); (pb/'same.txt').write_text('same')
            (pa/'gone.txt').write_text('gone')
            (pb/'new.txt').write_text('new')
            (pa/'oldname.txt').write_text('rename me'); (pb/'newname.txt').write_text('rename me')
            (pa/'change.txt').write_text('old'); (pb/'change.txt').write_text('new text')
            e=compare_trees(scan_tree(pa,hash_files=True),scan_tree(pb,hash_files=True))
            s=summarize(e)
            self.assertEqual(s['added'],1); self.assertEqual(s['removed'],1); self.assertEqual(s['renamed'],1); self.assertEqual(s['modified'],1); self.assertEqual(s['unchanged'],1)

if __name__=='__main__': unittest.main()