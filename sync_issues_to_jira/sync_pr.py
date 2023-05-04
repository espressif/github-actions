#!/usr/bin/env python3
#
# Copyright 2019 Espressif Systems (Shanghai) PTE LTD
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
from github import Github
from sync_issue import _find_jira_issue, _create_jira_issue


def sync_remain_prs(jira):
    """
    Sync remain PRs (i.e. PRs without any comments) to Jira
    """
    github = Github(os.environ['GITHUB_TOKEN'])
    repo = github.get_repo(os.environ['GITHUB_REPOSITORY'])
    prs = repo.get_pulls(state="open", sort="created", direction="desc")
    for pr in prs:
        if not repo.has_in_collaborators(pr.user.login) and not pr.comments:
            # mock a github issue using current PR
            gh_issue = {"pull_request": True,
                        "labels": [{"name": label.name} for label in pr.labels],
                        "number": pr.number,
                        "title": pr.title,
                        "html_url": pr.html_url,
                        "user": {"login": pr.user.login},
                        "state": pr.state,
                        "body": pr.body}
            issue = _find_jira_issue(jira, gh_issue)
            if issue is None:
                _create_jira_issue(jira, gh_issue)
