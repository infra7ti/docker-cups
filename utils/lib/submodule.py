# -*- coding: utf-8 -*-
##
# @file submodule.py
# @brief Object-oriented Submodule Manager supporting discrete actions and json matrices.
#
# SPDX-FileCopyrightText: 2026 INFRA7 Serviços em TI
# SPDX-License-Identifier: GPL-2.0-or-later
##

import argparse
import json
import subprocess
import sys
import shutil
from pathlib import Path

from minicli import Cli


class SubmoduleError(Exception):
    """Custom exception layer for submodule orchestration failures."""
    pass


class SubmoduleModel:
    """Data abstraction structure representing a single submodule footprint."""

    def __init__(self, name, path, repository, ref="main", folder="all"):
        self.name = name
        self.path = Path(path)
        self.repository = repository
        self.ref = ref
        self.folder = folder


class SubmoduleManager:
    """Core domain service handling multi-repository lifecycle synchronization."""

    @staticmethod
    def run_cmd(cmd, cwd=None):
        """Executes a shell command or raises a controlled exception on breakdown."""
        result = subprocess.run(cmd, shell=True, cwd=cwd, text=True, capture_output=True)
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else f"Exit code {result.returncode}"
            raise SubmoduleError(f"Command failed: {cmd} -> {error_msg}")
        return result.stdout.strip()

    @staticmethod
    def is_valid_sha1(hex_str):
        """Validates if a targeted reference conforms to a hexadecimal SHA-1 string."""
        clean_str = hex_str.strip()
        return len(clean_str) >= 7 and all(c in "0123456789abcdefABCDEF" for c in clean_str)

    def add(self, sub: SubmoduleModel):
        """Maps and provisions an independent cloned slice into the repository tree."""
        Cli.item(f"Mapping submodule '{Cli.highlight(sub.name)}' into '{Cli.path(sub.path)}'...")
        git_dir = Path(".git") / "modules" / sub.name

        match (git_dir.exists(), sub.path.exists()):
            case (True, False):
                Cli.item("Metadata found, but working tree missing. Re-linking...", nested=True)
                sub.path.mkdir(parents=True, exist_ok=True)
                with open(sub.path / ".git", "w") as f:
                    f.write(f"gitdir: ../.git/modules/{sub.name}\n")
            case (False, _):
                Cli.item("Cloning remote metadata directly to git storage (no-checkout)...", nested=True)
                git_dir.parent.mkdir(parents=True, exist_ok=True)
                self.run_cmd(f"git clone --no-checkout --separate-git-dir {git_dir} {sub.repository} {sub.path}")

        self.run_cmd(f"git config --file .gitmodules submodule.{sub.name}.path {sub.path}")
        self.run_cmd(f"git config --file .gitmodules submodule.{sub.name}.url {sub.repository}")
        self.run_cmd(f"git config --file .gitmodules submodule.{sub.name}.ref {sub.ref}")
        self.run_cmd(f"git config --file .gitmodules submodule.{sub.name}.folder {sub.folder}")
        self.run_cmd(f"git config --file .gitmodules submodule.{sub.name}.ignore all")
        self.run_cmd(f"git config submodule.{sub.name}.url {sub.repository}")
        self.run_cmd(f"git config submodule.{sub.name}.ref {sub.ref}")

        Cli.item("Fetching remote references...", nested=True)
        self.run_cmd("git fetch --tags origin", cwd=sub.path)

        if self.is_valid_sha1(sub.ref):
            self.run_cmd(f"git checkout --force {sub.ref}", cwd=sub.path)
        else:
            check_branch = subprocess.run(
                f"git ls-remote --heads origin {sub.ref}",
                shell=True, capture_output=True, text=True, cwd=sub.path
            )
            if check_branch.stdout.strip():
                self.run_cmd(f"git checkout -B {sub.ref} origin/{sub.ref}", cwd=sub.path)
            else:
                self.run_cmd(f"git checkout --force {sub.ref}", cwd=sub.path)

        match sub.folder.lower():
            case "all":
                self.run_cmd("git read-tree -mu HEAD", cwd=sub.path)
            case _:
                self.run_cmd(f"git read-tree -m -u HEAD:{sub.folder}", cwd=sub.path)

        self.run_cmd(f"git add .gitmodules {sub.path}")
        Cli.status("success", f"Submodule '{Cli.highlight(sub.name)}' configured successfully.", 2)

    def update(self, local_path):
        """Synchronizes and updates the target tracking node reference."""
        path_str = str(local_path)
        sub_name = self.run_cmd(f"git config --file .gitmodules --get-regexp 'submodule\\..*\\.path' '{path_str}' | cut -d'.' -f2")

        if not sub_name or not Path(local_path).exists():
            raise SubmoduleError(f"Submodule at path '{local_path}' is not initialized or invalid.")

        Cli.item(f"Synchronizing submodule '{Cli.highlight(sub_name)}'...")
        target_ref = self.run_cmd(f"git config --file .gitmodules submodule.{sub_name}.ref")
        self.run_cmd("git fetch --tags origin", cwd=local_path)

        if self.is_valid_sha1(target_ref):
            self.run_cmd(f"git checkout --force {target_ref}", cwd=local_path)
        else:
            check_branch = subprocess.run(
                f"git ls-remote --heads origin {target_ref}",
                shell=True, capture_output=True, text=True, cwd=local_path
            )
            if check_branch.stdout.strip():
                self.run_cmd(f"git submodule update --remote --force {local_path}")
                self.run_cmd(f"git checkout -B {target_ref} origin/{target_ref}", cwd=local_path)
            else:
                self.run_cmd(f"git checkout --force {target_ref}", cwd=local_path)

        check_folder = subprocess.run(
            f"git config --file .gitmodules submodule.{sub_name}.folder",
            shell=True, capture_output=True, text=True
        )
        remote_folder = check_folder.stdout.strip() if check_folder.returncode == 0 else "all"

        match remote_folder.lower():
            case "all" | "":
                self.run_cmd("git read-tree -mu HEAD", cwd=local_path)
            case _:
                self.run_cmd(f"git read-tree -m -u HEAD:{remote_folder}", cwd=local_path)

        Cli.status("success", f"Synchronization completed for target '{Cli.highlight(sub_name)}'.", 2)

    def remove(self, name, local_path):
        """Expunges layout components and purges metadata containers completely."""
        sub_path = Path(local_path)
        sub_name = name

        if not sub_name:
            if sub_path.exists():
                try:
                    sub_name = self.run_cmd(f"git config --file .gitmodules --get-regexp 'submodule\\..*\\.path' '{sub_path}' | cut -d'.' -f2")
                except Exception:
                    sub_name = sub_path.name
            else:
                sub_name = sub_path.name

        Cli.item(f"Removing submodule mapping: {Cli.highlight(sub_name)}")

        subprocess.run(f"git rm --cached -f {sub_path}", shell=True, capture_output=True)
        subprocess.run(f"git config --file .gitmodules --remove-section submodule.{sub_name}", shell=True, capture_output=True)
        subprocess.run(f"git config --remove-section submodule.{sub_name}", shell=True, capture_output=True)

        if sub_path.exists() or subprocess.run(f"git ls-files --error-unmatch {sub_path}", shell=True, capture_output=True).returncode == 0:
            subprocess.run(f"git rm -rf {sub_path}", shell=True, capture_output=True)

        if sub_path.is_dir() and not (sub_path / ".git").is_dir():
            shutil.rmtree(sub_path, ignore_errors=True)

        git_internal_dir = Path(".git") / "modules" / sub_name
        if git_internal_dir.exists():
            shutil.rmtree(git_internal_dir, ignore_errors=True)

        if Path(".gitmodules").exists() and Path(".gitmodules").stat().st_size == 0:
            Path(".gitmodules").unlink()

        Cli.status("success", f"Submodule '{Cli.highlight(sub_name)}' completely expunged.", 2)

    def list_configured(self):
        """Extracts and prints all tracked submodules directly from the .gitmodules state."""
        if not Path(".gitmodules").exists():
            Cli.status("notice", "No active .gitmodules tracking file found in workspace.")
            return []

        lines = self.run_cmd("git config --file .gitmodules --get-regexp 'submodule\\..*\\.path' || true")
        if not lines:
            Cli.status("notice", "No configured submodules found inside the index tracking list.")
            return []

        configured = []
        Cli.item(f"Looking for configured GIT submodules...")
        for line in lines.splitlines():
            if not line.strip():
                continue
            parts = line.split(" ")
            key = parts[0]
            val = parts[1]
            name = key.split(".")[1]
            configured.append({"name": name, "path": val})
            Cli.status("info", f"Node {Cli.highlight(name)} was mapped at {Cli.path(val)}.", 2)
        return configured

    def prune_obsolete_against_manifest(self, config_file_path):
        """Compares current tree against the json file and prunes anything missing from it."""
        if not Path(".gitmodules").exists():
            return

        with open(config_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        manifest_submodules = data.get("submodules", [])
        manifest_names = {item.get("name") for item in manifest_submodules if "name" in item}

        lines = subprocess.run("git config --file .gitmodules --get-regexp 'submodule\\..*\\.path' || true",
                               shell=True, text=True, capture_output=True).stdout.strip()

        for line in lines.splitlines():
            if line:
                parts = line.split(" ")
                active_name = parts[0].split(".")[1]
                path_to_remove = parts[1]
                if active_name not in manifest_names:
                    self.remove(active_name, path_to_remove)

    def sync_config(self, config_file_path, action):
        """Processes the submodules layout matrix executing strictly requested explicit actions."""
        config_path = Path(config_file_path)
        if not config_path.exists():
            raise SubmoduleError(f"Target manifest definition descriptor missing: {config_file_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        manifest_submodules = data.get("submodules", [])

        current_configured = {}
        if Path(".gitmodules").exists():
            lines = subprocess.run("git config --file .gitmodules --get-regexp 'submodule\\..*\\.path' || true",
                                   shell=True, text=True, capture_output=True).stdout.strip()
            for line in lines.splitlines():
                if line:
                    parts = line.split(" ")
                    current_configured[parts[0].split(".")[1]] = parts[1]

        match action.lower().strip():
            case "add":
                for item in manifest_submodules:
                    name = item.get("name")
                    if name not in current_configured:
                        sub_model = SubmoduleModel(name, item.get("path"), item.get("repository"), item.get("ref", "main"), item.get("folder", "all"))
                        self.add(sub_model)

            case "update":
                for item in manifest_submodules:
                    name = item.get("name")
                    if name in current_configured:
                        sub_model = SubmoduleModel(name, item.get("path"), item.get("repository"), item.get("ref", "main"), item.get("folder", "all"))
                        self.run_cmd(f"git config --file .gitmodules submodule.{name}.ref {sub_model.ref}")
                        self.run_cmd(f"git config --file .gitmodules submodule.{name}.folder {sub_model.folder}")
                        self.update(sub_model.path)

            case "remove":
                for item in manifest_submodules:
                    name = item.get("name")
                    if name in current_configured:
                        self.remove(name, current_configured[name])

            case _:
                raise SubmoduleError(f"Unsupported manual configuration routine action: '{action}'")


def main():
    parser = argparse.ArgumentParser(description="Object-oriented structural Git submodule manager.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Command: add (Manual entry parameters restored)
    p_add = subparsers.add_parser("add")
    p_add.add_argument("-R", "--repository", required=True, help="Remote repository URL")
    p_add.add_argument("-f", "--folder", default="all", help="Remote folder path to slice")
    p_add.add_argument("-r", "--ref", default="main", help="Target git branch, tag or commit SHA-1")
    p_add.add_argument("-n", "--name", help="Submodule semantic signature name")
    p_add.add_argument("path", help="Local tracking layout directory path")

    # Command: update (Manual entry parameters restored)
    p_update = subparsers.add_parser("update")
    p_update.add_argument("path", help="Local tracking directory path to synchronize")

    # Command: remove (Manual entry parameters restored)
    p_remove = subparsers.add_parser("remove")
    p_remove.add_argument("-n", "--name", help="Submodule semantic signature name")
    p_remove.add_argument("path", help="Local tracking layout directory path")

    # Command: list
    subparsers.add_parser("list")

    # Command: config (Strictly maps: config -c|--config cfgfile <action>)
    p_config = subparsers.add_parser("config")
    p_config.add_argument("-c", "--config", required=True, dest="cfgfile", help="Path to targeted submodules JSON file")
    p_config.add_argument("action", choices=["add", "update", "remove"], help="Explicit positional target action")

    args = parser.parse_args()
    mgr = SubmoduleManager()

    try:
        match args.command:
            case "add":
                model = SubmoduleModel(args.name if args.name else Path(args.path).name, args.path, args.repository, args.ref, args.folder)
                mgr.add(model)
            case "update":
                mgr.update(args.path)
            case "remove":
                mgr.remove(args.name, args.path)
            case "list":
                mgr.list_configured()
            case "config":
                mgr.sync_config(args.cfgfile, args.action)
    except SubmoduleError as err:
        Cli.status("error", str(err))
        sys.exit(1)


if __name__ == "__main__":
    main()

