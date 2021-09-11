import os
import sys

from JciHitachi import __author__, __version__


git_repo_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.join(git_repo_path, "docs", "source"))

import conf


class TestSanity:
    def test_annotions_consistency(self):
        assert __author__ == conf.author
        assert f"v{__version__}" == conf.release
