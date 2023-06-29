#!/usr/bin/env python
#
# SPDX-FileCopyrightText: 2023 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0
#
import argparse
import collections
import contextlib
import logging
import os
import re
import sys
import typing
from pathlib import Path

import git
import github

DEFAULT_TAG_VERSION_REGEX = r"v?(\d+)\.(\d+)(?:\.(\d+))?$"
REMOTE = "origin"

IdfComponentVersion = collections.namedtuple(
    "IdfComponentVersion", ["major", "minor", "patch"]
)

SubmoduleConfig = collections.namedtuple(
    "SubmoduleConfig",
    [
        "submodule",
        "branch",
        "tag_glob",
        "include_lightweight",
        "manifest",
        "ver_regex",
        "url",
    ],
)


def find_latest_remote_tag(
    repo: git.Repo, branch: str, tag_glob: str, include_lightweight: bool
) -> git.TagReference:
    """
    Find the latest tag which matches the given glob pattern on the remote branch
    """
    remote_branch = f"{REMOTE}/{branch}"
    describe_args = [
        "--abbrev=0",
        remote_branch,
    ]
    if tag_glob:
        describe_args += ["--match", tag_glob]
    if include_lightweight:
        describe_args += ["--tags"]
    try:
        latest_tag_name = repo.git.describe(describe_args)
    except git.GitCommandError as e:
        raise RuntimeError(
            f"Failed to run 'git describe {' '.join(describe_args)}': {e.stderr}"
        )
    return repo.tag(latest_tag_name)


def is_commit_ahead_of_tag(
    repo: git.repo, commit: git.Commit, tag: git.TagReference
) -> bool:
    """
    Returns true if "commit" is more recent than "tag"
    """
    try:
        repo.git.describe(commit.hexsha, tags=True, match=tag.name)
        return True
    except git.GitCommandError:
        return False


def update_submodule_pointer(
    repo: git.repo, submodule: git.Submodule, new_tag: git.TagReference
) -> None:
    """
    Change the submodule pointer to the specified tag and add this change to the index
    of the parent repository.
    """
    submodule.binsha = new_tag.commit.binsha
    submodule.update()
    repo.index.add([submodule])


def finish_commit(
    repo: git.Repo, submodule: git.Submodule, new_tag_name: str, commit_desc: str
) -> None:
    """
    When changes have already been staged, this function creates a commit describing the
    upgrade to the new version.

    """
    commit_msg = f"{submodule.path}: Update to {new_tag_name}\n\n{commit_desc}"
    repo.index.commit(commit_msg)
    logging.info(f'Created commit: "{commit_msg}"')


def get_version_from_tag(tag_name: str, version_regex: str) -> IdfComponentVersion:
    match = re.match(version_regex, tag_name)
    if not match:
        raise ValueError(
            f'Tag "{tag_name}" doesn\'t match version regex "{version_regex}"'
        )

    match_groups_num = len(list(filter(lambda g: g is not None, match.groups())))
    if match_groups_num == 2:
        patch = 0
    elif match_groups_num == 3:
        patch = int(match.group(3))
    else:
        raise ValueError(
            f"Regular expression must have 2 or 3 match groups, got {match_groups_num}"
        )

    return IdfComponentVersion(
        major=int(match.group(1)), minor=int(match.group(2)), patch=patch
    )


def update_idf_component_yml_version(idf_cmp_yml: Path, ver: IdfComponentVersion):
    """Rewrite the version value in the specified idf_component.yml file with the given version"""
    with open(idf_cmp_yml, "r", encoding="utf-8") as f:
        lines = f.readlines()

    version_regex = re.compile(
        r'^(?P<head>version\s*:\s*)"[^"]+"(?P<tail>[ \t]*(#.*)?)(\n)?'
    )
    version_found = False
    for i, line in enumerate(lines):
        match = re.match(version_regex, line)
        if match and version_found:
            raise ValueError("Duplicate version lines in idf_component.yml")
        elif match:
            version_found = True
            head = match.group("head")
            tail = match.group("tail")
            new_line = f'{head}"{ver.major}.{ver.minor}.{ver.patch}"{tail}\n'
            lines[i] = new_line
    if not version_found:
        raise ValueError(f"No 'version: \"x.y.z\"' line in {idf_cmp_yml}")

    with open(idf_cmp_yml, "w", encoding="utf-8") as fw:
        fw.writelines(lines)


def get_commit_log(
    repo: git.Repo, remote_url: str, from_sha: str, to_sha: str
) -> typing.List[str]:
    if remote_url.startswith("https://github.com/"):
        url_without_dot_git = remote_url.removesuffix(".git")
        log_format = f"- {url_without_dot_git}/commit/%h: %s"
    else:
        log_format = f"- %h: %s%n"

    lines = repo.git.log(f"{from_sha}...{to_sha}", format=log_format).split("\n")
    return lines


@contextlib.contextmanager
def reset_to_original_branch(repo: git.Repo):
    orig_branch = repo.active_branch
    try:
        yield
    finally:
        logging.info(f"Reverting back to {orig_branch}")
        repo.git.checkout(orig_branch)
        logging.info("Resetting submodules")
        repo.git.submodule("update", "--recursive")


def update_one_submodule(
    repo: git.Repo, config: SubmoduleConfig, dry_run: bool = False
) -> typing.Optional[str]:
    submodule = repo.submodule(config.submodule)
    logging.info(f"Checking for updates to {submodule.path}")

    sub_repo = submodule.module()
    current_desc = sub_repo.git.describe(sub_repo.commit().hexsha, abbrev=8, tags=True)
    logging.info(f"Current submodule points to: {current_desc} ({submodule.hexsha})")

    sub_repo.remote(REMOTE).fetch(config.branch, tags=True)
    latest_tag = find_latest_remote_tag(
        sub_repo, config.branch, config.tag_glob, config.include_lightweight
    )
    logging.info(
        f"Latest tag on {config.branch}: {latest_tag.name} ({latest_tag.commit.hexsha})"
    )

    if latest_tag.commit.hexsha == submodule.hexsha:
        logging.info("Already at the latest tag, nothing to do.")
        return None

    if is_commit_ahead_of_tag(sub_repo, sub_repo.commit(), latest_tag):
        logging.info("Latest tag is behind current commit, nothing to do")
        return None

    commit_log = get_commit_log(
        sub_repo, config.url, sub_repo.commit().hexsha, latest_tag.commit.hexsha
    )
    commit_desc = (
        f"Changes between {sub_repo.commit().hexsha} and {latest_tag.commit.hexsha}:\n\n"
        + "\n".join(commit_log)
    )

    if dry_run:
        logging.info(f"Would update {submodule.path} to {latest_tag.name}")
        logging.info(f"Commit message: {commit_desc}")
        return None

    logging.info(f"Updating {submodule.path} to {latest_tag.name}")
    update_submodule_pointer(repo, submodule, latest_tag)

    idf_cmp_yml = config.manifest
    if idf_cmp_yml:
        cmp_ver = get_version_from_tag(latest_tag.name, config.ver_regex)
        logging.info(f"Updating component version in {idf_cmp_yml} to {cmp_ver}")
        update_idf_component_yml_version(Path(repo.working_dir) / idf_cmp_yml, cmp_ver)
        repo.index.add([idf_cmp_yml])

    simple_submodule_name = submodule.path.split("/")[-1]
    update_branch_name = f"update/{simple_submodule_name}_{latest_tag}"
    logging.info(
        f"Creating branch {update_branch_name} (at {repo.commit().hexsha}, {repo.active_branch})"
    )
    repo.create_head(update_branch_name, commit=repo.commit().hexsha)
    logging.info(f"Checking out {update_branch_name}")
    repo.git.checkout(update_branch_name)

    finish_commit(repo, submodule, latest_tag.name, commit_desc=commit_desc)

    return update_branch_name


def push_to_remote(repo: git.Repo, remote_name: str, branch_name: str) -> None:
    logging.info(f"Pushing {branch_name} to {remote_name}...")
    repo.git.push(remote_name, f"{branch_name}:{branch_name}", force=True)


def open_github_pr(dest_repo: str, branch_name: str, pr_text: str) -> None:
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        raise RuntimeError("GITHUB_TOKEN environment variable must be set")
    gh = github.Github(github_token)
    repo = gh.get_repo(dest_repo)
    commit_msg_lines = pr_text.split("\n")
    pr_title = commit_msg_lines[0]
    pr_text = "\n".join(commit_msg_lines[1:])
    logging.info(f"Opening a pull request in {dest_repo}: '{pr_title}'")
    repo.create_pull(
        title=pr_title,
        body=pr_text,
        base="master",
        head=branch_name,
        maintainer_can_modify=True,
    )


def get_config_bool_or_default(
    config_reader: typing.Any, config_name: str, default: bool
) -> bool:
    raw_val = config_reader.get(config_name, fallback=None)
    if raw_val is None:
        return default
    if raw_val == "false":
        return False
    if raw_val == "true":
        return True
    raise ValueError(f"Invalid bool value for config {config_name}: {raw_val}")


def load_configs(repo: git.Repo) -> typing.List[SubmoduleConfig]:
    configs: typing.List[SubmoduleConfig] = []
    for sub in repo.submodules:
        with sub.config_reader() as config_reader:
            path = config_reader.get("path")
            assert path
            autoupdate_enable = config_reader.get("autoupdate", fallback=None)
            if not autoupdate_enable or autoupdate_enable == "false":
                logging.info(f"Skipping submodule {path}, autoupdate not enabled")
                continue

            url = config_reader.get("url")
            branch = config_reader.get("autoupdate-branch")
            include_lightweight = get_config_bool_or_default(
                config_reader, "autoupdate-include-lightweight", default=False
            )
            manifest = config_reader.get("autoupdate-manifest", fallback=None)
            tag_glob = config_reader.get("autoupdate-tag-glob", fallback=None)
            ver_regex = config_reader.get("autoupdate-ver-regex", fallback=None)
            if ver_regex:
                ver_regex = ver_regex.replace("\\\\", "\\")

            cfg = SubmoduleConfig(
                submodule=path,
                branch=branch,
                tag_glob=tag_glob,
                include_lightweight=include_lightweight,
                manifest=manifest,
                ver_regex=ver_regex,
                url=url,
            )
            configs.append(cfg)

    return configs


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Only check, don't perform any updates",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Don't exit immediately if the repository has unstaged changes",
    )
    parser.add_argument(
        "--push-to-remote",
        default="origin",
        help="Name of the remote to push the update to",
    )
    parser.add_argument(
        "--open-github-pr-in",
        default=None,
        help="Repository (owner/name) to open PRs in",
    )
    parser.add_argument(
        "--repo",
        type=lambda p: Path(p),
        help="Git repository path"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    repo = git.Repo(args.repo)

    configs = load_configs(repo)

    if repo.is_dirty() and not args.allow_dirty:
        logging.error(f"Repository at {args.repo} is dirty, aborting!")
        raise SystemExit(1)

    for config in configs:
        with reset_to_original_branch(repo):
            update_branch_name = update_one_submodule(repo, config, args.dry_run)
            if update_branch_name is None:
                continue

            if args.push_to_remote:
                push_to_remote(repo, args.push_to_remote, update_branch_name)

                if args.open_github_pr_in:
                    open_github_pr(
                        args.open_github_pr_in,
                        update_branch_name,
                        repo.commit().message,
                    )


if __name__ == "__main__":
    main()
