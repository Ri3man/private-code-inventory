"""Behavior and privacy tests using temporary, synthetic Git repositories."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "private-code-inventory.py"
SPEC = importlib.util.spec_from_file_location("inventory", SCRIPT)
inventory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inventory)


class InventoryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="synthetic-private-owner-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "secret-project-name"
        self.repo.mkdir()
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                         "GIT_AUTHOR_NAME": "Sensitive Owner", "GIT_COMMITTER_NAME": "Sensitive Owner",
                         "GIT_AUTHOR_EMAIL": "private-owner@example.invalid",
                         "GIT_COMMITTER_EMAIL": "private-owner@example.invalid"})
        self.git("init", "--quiet")

    def git(self, *args, repo=None, date=None):
        env = dict(self.env)
        if date:
            env.update({"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date})
        return subprocess.run(["git", "-C", str(repo or self.repo), *args],
                              env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              check=True).stdout

    def commit(self, date="2024-01-02T12:00:00Z"):
        self.git("add", "-A")
        self.git("commit", "--quiet", "--allow-empty", "-m", "PRIVATE COMMIT MESSAGE", date=date)

    def populated(self):
        files = {"src/payment-secret.py": "API_SECRET = 'do-not-disclose-content'\n",
                 "src/odd\tfile.js": "// sensitive content\n", ".env": "PASSWORD=never-report-me\n",
                 "keys/secret.pem": "private certificate contents\n", "LICENSE": "not a real licence\n",
                 "customer-name.customsecret": "customer data\n", "docs/说明.md": "internal text\n"}
        for name, contents in files.items():
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents)
        self.commit()
        self.git("remote", "add", "origin", "https://private-token@example.invalid/top-secret/repository.git")
        self.commit("2024-04-03T17:30:00Z")
        self.commit("2025-02-01T08:00:00Z")

    def test_aggregate_is_accurate_and_does_not_expose_source_or_identity(self):
        self.populated()
        # Working-tree changes are intentionally outside the inventory.
        (self.repo / "untracked-rust.rs").write_text("uncommitted sensitive text")
        before = self.git("status", "--porcelain=v1")
        report = inventory.inspect_repository(self.repo)
        tree, history = report["current_committed_tree"], report["history"]
        self.assertEqual(history["available_reachable_commits"], 3)
        self.assertEqual(history["earliest_observed_committer_date"], "2024-01-02T12:00:00+00:00")
        self.assertEqual(history["latest_observed_committer_date"], "2025-02-01T08:00:00+00:00")
        self.assertEqual(tree["tracked_files"], 7)
        self.assertEqual(tree["potentially_sensitive_filename_count"], 2)
        self.assertTrue(tree["license_document_present"])
        self.assertEqual(tree["file_types_by_extension"], {"Documentation": 1, "JavaScript": 1, "Other": 4, "Python": 1})
        self.assertEqual(before, self.git("status", "--porcelain=v1"))
        output = json.dumps(report) + inventory.as_markdown(report)
        for private_text in [str(self.root), "secret-project-name", "payment-secret", "Sensitive Owner",
                             "private-owner@", "private-token", "PRIVATE COMMIT MESSAGE", "API_SECRET",
                             "do-not-disclose-content", "customsecret", "customer-name", "never-report-me"]:
            self.assertNotIn(private_text, output)

    def test_empty_repository_and_sanitized_failure(self):
        report = inventory.inspect_repository(self.repo)
        self.assertEqual(report["history"]["available_reachable_commits"], 0)
        self.assertFalse(report["current_committed_tree"]["head_available"])
        invalid = self.root / "private-not-a-repository"
        invalid.mkdir()
        result = subprocess.run([sys.executable, str(SCRIPT), str(invalid)], text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertNotIn(str(invalid), result.stderr)
        self.assertIn("Inventory incomplete", result.stderr)

    def test_bare_and_shallow_repositories(self):
        self.populated()
        bare = self.root / "private-bare.git"
        self.git("clone", "--bare", str(self.repo), str(bare), repo=self.root)
        report = inventory.inspect_repository(bare)
        self.assertTrue(report["current_committed_tree"]["is_bare_repository"])
        self.assertEqual(report["history"]["available_reachable_commits"], 3)
        shallow = self.root / "private-shallow"
        self.git("clone", "--depth=1", self.repo.as_uri(), str(shallow), repo=self.root)
        report = inventory.inspect_repository(shallow)
        self.assertTrue(report["history"]["is_shallow"])
        self.assertEqual(report["history"]["available_reachable_commits"], 1)
        self.assertEqual(report["current_committed_tree"]["tracked_files"], 7)

    def test_subdirectory_cannot_silently_inventory_parent_repository(self):
        self.populated()
        with self.assertRaisesRegex(inventory.InventoryError, "repository root"):
            inventory.inspect_repository(self.repo / "src")

    def test_linked_worktree_root_is_supported(self):
        self.populated()
        worktree = self.root / "separate-worktree"
        self.git("worktree", "add", "--detach", str(worktree), "HEAD")
        report = inventory.inspect_repository(worktree)
        self.assertEqual(report["history"]["available_reachable_commits"], 3)
        self.assertEqual(report["current_committed_tree"]["tracked_files"], 7)

    def test_submodule_is_counted_without_traversal(self):
        self.populated()
        commit_hash = self.git("rev-parse", "HEAD").strip().decode()
        self.git("update-index", "--add", "--cacheinfo", "160000," + commit_hash + ",private-dependency")
        self.git("commit", "--quiet", "-m", "submodule metadata", date="2025-02-02T08:00:00Z")
        report = inventory.inspect_repository(self.repo)
        self.assertEqual(report["current_committed_tree"]["submodule_entries_not_traversed"], 1)
        self.assertEqual(report["current_committed_tree"]["tracked_files"], 7)

    def test_inherited_git_environment_cannot_redirect_inventory(self):
        self.populated()
        other = self.root / "different-private-repository"
        other.mkdir()
        self.git("init", "--quiet", repo=other)
        with patch.dict(os.environ, {"GIT_DIR": str(other / ".git"),
                                     "GIT_WORK_TREE": str(other), "GIT_CONFIG_COUNT": "1",
                                     "GIT_CONFIG_KEY_0": "core.fsmonitor",
                                     "GIT_CONFIG_VALUE_0": "unwanted-program"}):
            report = inventory.inspect_repository(self.repo)
        self.assertEqual(report["history"]["available_reachable_commits"], 3)

    def test_sample_limit_is_disclosed_and_markdown_cli_works(self):
        self.populated()
        with patch.object(inventory, "DATE_SAMPLE_LIMIT", 2):
            report = inventory.inspect_repository(self.repo)
        self.assertEqual(report["history"]["committer_dates_sampled"], 2)
        self.assertFalse(report["history"]["date_range_complete_for_available_history"])
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.repo), "--format", "markdown"],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Private-code preparation inventory", result.stdout)
        self.assertNotIn(str(self.repo), result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
