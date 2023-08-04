import os
import sys

from JciHitachi import __author__, __version__

git_repo_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
requirements_txt_path = os.path.join(git_repo_path, "requirements.txt")
requirements_test_txt_path = os.path.join(git_repo_path, "requirements_test.txt")

sys.path.append(git_repo_path)
sys.path.append(os.path.join(git_repo_path, "docs", "source"))

import conf

from setup import install_requires, tests_require


class TestSanity:
    def test_annotions_consistency(self):
        assert __author__ == conf.author
        assert f"v{__version__}" == conf.release

    def test_install_requirements_consistency(self):
        with open(requirements_txt_path, "r", encoding="utf-8") as f:
            req_txt = [req for req in f.read().split("\n") if req[0] != "-"]
        assert set(install_requires) == set(req_txt)

    def test_test_requirements_consistency(self):
        with open(requirements_test_txt_path, "r", encoding="utf-8") as f:
            req_txt = [req for req in f.read().split("\n") if req[0] != "-"]
        assert set(tests_require) == set(req_txt)
