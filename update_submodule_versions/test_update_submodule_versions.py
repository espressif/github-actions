# SPDX-FileCopyrightText: 2023 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0
import tempfile
import textwrap
import unittest

from git import Repo, Commit

from update_submodule_versions import *


class UpdateSubmoduleVersionsTest(unittest.TestCase):
    def setUp(self) -> None:
        # create the repo for a dependency
        self.dependency_dir = Path(tempfile.mkdtemp())
        self.dependency_repo = Repo.init(self.dependency_dir)

        # add a file and make the first commit
        dependency_readme_file = self.dependency_dir / "README.md"
        dependency_readme_file.write_text("This is a dependency\n")
        self.dependency_repo.index.add([dependency_readme_file.name])
        dep_commit = self.dependency_repo.index.commit(
            "initial commit of the dependency"
        )
        self.dependency_repo.create_head("main", commit=dep_commit.hexsha)

        # create the "project" repo where the submodule will be added
        self.project_dir = Path(tempfile.mkdtemp())
        self.project_repo = Repo.init(self.project_dir.absolute())

        # add the dependency as a submodule and commit it
        self.submodule = self.project_repo.create_submodule(
            "dependency", "dependency", url=self.dependency_dir, branch="main"
        )
        self.project_repo.index.commit("added a dependency as a submodule")

        self.addCleanup(self.dependency_dir)
        self.addCleanup(self.project_dir)

    def create_commit(self, repo: Repo, filename: str, commit_msg: str) -> Commit:
        """Make a commit in the given repo, creating an empty file"""
        file_path = Path(repo.working_tree_dir) / filename
        file_path.touch()
        repo.index.add([filename])
        return repo.index.commit(message=commit_msg)

    def tag_dependency(self, tag_name: str) -> Commit:
        """Make a commit in the dependency and tag it with the given name"""
        dep_commit = self.create_commit(
            self.dependency_repo, f"release_{tag_name}.md", f"Release {tag_name}"
        )
        self.dependency_repo.create_tag(
            tag_name, dep_commit.hexsha, message=f"Release {tag_name}"
        )
        return dep_commit

    def update_dependency_submodule_to(self, commit: Commit, commit_msg: str):
        submodule = self.project_repo.submodule("dependency")
        submodule.binsha = commit.binsha
        submodule.update()
        self.project_repo.index.add([submodule])
        self.project_repo.index.commit(commit_msg)

    def test_can_update_manually(self):
        """This is just a test to check that the setUp and above functions work okay"""
        self.create_commit(self.dependency_repo, "1.txt", "Added 1.txt")
        submodule_commit = self.tag_dependency("v1.0")
        self.update_dependency_submodule_to(
            submodule_commit, "update submodule to v1.0"
        )
        self.assertTrue((self.project_dir / "dependency" / "1.txt").exists())
        self.assertEqual(
            "v1.0",
            self.project_repo.git.submodule("--quiet foreach git describe".split()),
        )

    def test_find_latest_remote_tag(self):
        """Check that find_latest_remote_tag function finds the tagged commit"""

        # Create a tag, check that it is found on the right commit
        first_commit = self.create_commit(self.dependency_repo, "1.txt", "Added 1.txt")
        self.create_commit(self.dependency_repo, "2.txt", "Added 2.txt")
        v2_release_commit = self.tag_dependency("v2.0")
        self.create_commit(self.dependency_repo, "3.txt", "Added 3.txt")
        tag_found = find_latest_remote_tag(self.submodule, "main", "v*")
        self.assertEqual(v2_release_commit.hexsha, tag_found.commit.hexsha)

        # Create a tag on an older commit, check that the most recent tag
        # (in branch sequential order) is found, not the most recent one
        # in chronological order
        self.dependency_repo.create_tag(
            "v1.0", first_commit.hexsha, message=f"Release v1.0"
        )
        tag_found = find_latest_remote_tag(self.submodule, "main", "v*")
        self.assertEqual(v2_release_commit.hexsha, tag_found.commit.hexsha)

        # Check that the wildcard is respected, by looking specifically for v1* tags
        tag_found = find_latest_remote_tag(self.submodule, "main", "v1*")
        self.assertEqual(first_commit.hexsha, tag_found.commit.hexsha)

        # Create a newer tag on another branch, check that it is not found
        self.dependency_repo.create_head(
            "release/v2.0", commit=v2_release_commit.hexsha
        )
        self.dependency_repo.git.checkout("release/v2.0")
        self.create_commit(self.dependency_repo, "2_1.txt", "Added 2_1.txt")
        v2_1_release_commit = self.tag_dependency("v2.1")

        tag_found = find_latest_remote_tag(self.submodule, "main", "v*")
        self.assertEqual(v2_release_commit.hexsha, tag_found.commit.hexsha)

        # But the newest tag should be found if we specify the release branch
        tag_found = find_latest_remote_tag(self.submodule, "release/v2.0", "v*")
        self.assertEqual(v2_1_release_commit.hexsha, tag_found.commit.hexsha)


class VersionFromTagTest(unittest.TestCase):
    def test_version_from_tag(self):
        self.assertEqual(
            IdfComponentVersion(1, 2, 3),
            get_version_from_tag("v1.2.3", DEFAULT_TAG_VERSION_REGEX),
        )
        self.assertEqual(
            IdfComponentVersion(1, 2, 3),
            get_version_from_tag("1.2.3", DEFAULT_TAG_VERSION_REGEX),
        )
        self.assertEqual(
            IdfComponentVersion(1, 2, 0),
            get_version_from_tag("1.2", DEFAULT_TAG_VERSION_REGEX),
        )
        self.assertEqual(
            IdfComponentVersion(2, 4, 9),
            get_version_from_tag("R_2_4_9", r"R_(\d+)_(\d+)_(\d+)"),
        )

        with self.assertRaises(ValueError):
            get_version_from_tag("v1.2.3-rc1", DEFAULT_TAG_VERSION_REGEX)
        with self.assertRaises(ValueError):
            get_version_from_tag("qa-test-v1.2.3", DEFAULT_TAG_VERSION_REGEX)
        with self.assertRaises(ValueError):
            get_version_from_tag("v1.2.3.4", DEFAULT_TAG_VERSION_REGEX)
        with self.assertRaises(ValueError):
            get_version_from_tag("v1", DEFAULT_TAG_VERSION_REGEX)


class UpdateIDFComponentYMLVersionTest(unittest.TestCase):
    def update_manifest(self, orig_yaml: str, new_ver: IdfComponentVersion):
        with tempfile.NamedTemporaryFile("a+") as manifest_file:
            manifest_file.write(orig_yaml)
            manifest_file.flush()
            update_idf_component_yml_version(Path(manifest_file.name), new_ver)
            manifest_file.seek(0)
            return manifest_file.read()

    def test_update_manifest_version(self):
        self.assertEqual(
            textwrap.dedent(
                """
                # this is a comment
                version: "2.0.1"
            """
            ),
            self.update_manifest(
                textwrap.dedent(
                    """
                # this is a comment
                version: "1.2.0"
            """
                ),
                IdfComponentVersion(2, 0, 1),
            ),
        )

        self.assertEqual(
            textwrap.dedent(
                """
                repository: "https://github.com/espressif/idf-extra-components.git"
                version: "2.0.2"
            """
            ),
            self.update_manifest(
                textwrap.dedent(
                    """
                repository: "https://github.com/espressif/idf-extra-components.git"
                version: "2.0.1~1"
            """
                ),
                IdfComponentVersion(2, 0, 2),
            ),
        )

        self.assertEqual(
            textwrap.dedent(
                """
                        repository: "https://github.com/espressif/idf-extra-components.git"
                        version: "4.3.1"
                    """
            ),
            self.update_manifest(
                textwrap.dedent(
                    """
                        repository: "https://github.com/espressif/idf-extra-components.git"
                        version: "4.3.1~1-rc.1"
                    """
                ),
                IdfComponentVersion(4, 3, 1),
            ),
        )

        with self.assertRaises(ValueError):
            self.update_manifest(
                textwrap.dedent(
                    """
                repository: "https://github.com/espressif/idf-extra-components.git"
                # no version tag
                """
                ),
                IdfComponentVersion(1, 0, 0),
            )

        with self.assertRaises(ValueError):
            self.update_manifest(
                textwrap.dedent(
                    """
                version: "0.1.0"
                repository: "https://github.com/espressif/idf-extra-components.git"
                version: "0.1.1"
                """
                ),
                IdfComponentVersion(1, 0, 0),
            )

        self.assertEqual(
            textwrap.dedent(
                """
                # version: "1.0.0"
                version: "2.0.1"
            """
            ),
            self.update_manifest(
                textwrap.dedent(
                    """
                # version: "1.0.0"
                version: "1.2.0"
            """
                ),
                IdfComponentVersion(2, 0, 1),
            ),
        )

        self.assertEqual(
            textwrap.dedent(
                """
                repository: "https://github.com/espressif/idf-extra-components.git"
                version: "2.0.1"   # trailing comment
            """
            ),
            self.update_manifest(
                textwrap.dedent(
                    """
                repository: "https://github.com/espressif/idf-extra-components.git"
                version: "1.2.0"   # trailing comment
            """
                ),
                IdfComponentVersion(2, 0, 1),
            ),
        )

        # check that we add a newline in case version is on the last line and
        # the line was missing a newline
        self.assertEqual(
            textwrap.dedent(
                """
                repository: "https://github.com/espressif/idf-extra-components.git"
                version: "2.0.1"   # no newline
            """
            ),
            self.update_manifest(
                textwrap.dedent(
                    """
                repository: "https://github.com/espressif/idf-extra-components.git"
                version: "1.2.0"   # no newline"""
                ),
                IdfComponentVersion(2, 0, 1),
            ),
        )


if __name__ == "__main__":
    unittest.main()
