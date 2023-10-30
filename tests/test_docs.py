import os
import unittest
from sphinx.application import Sphinx
import multiprocessing

n_cpu = multiprocessing.cpu_count()


class TestDoc(unittest.TestCase):

    @property
    def path_to_docs(self):
        dirname, file_name = os.path.split(os.path.abspath(__file__))
        return os.path.sep.join(dirname.split(os.path.sep)[:-1] + ["docs"])

    def test_html(self):
        src_dir = config_dir = self.path_to_docs
        output_dir = os.path.sep.join([src_dir, "_build", "html"])
        doctree_dir = os.path.sep.join([src_dir, "_build", "doctree"])
        app = Sphinx(src_dir, config_dir, output_dir, doctree_dir, buildername="html", warningiserror=False, parallel=n_cpu)
        app.build()

    def test_linkcheck(self):
        src_dir = config_dir = self.path_to_docs
        output_dir = os.path.sep.join([src_dir, "_build", "linkcheck"])
        doctree_dir = os.path.sep.join([src_dir, "_build", "doctree"])
        app = Sphinx(src_dir, config_dir, output_dir, doctree_dir, buildername="linkcheck", warningiserror=False, parallel=n_cpu)
        app.build()


if __name__ == '__main__':
    unittest.main()
