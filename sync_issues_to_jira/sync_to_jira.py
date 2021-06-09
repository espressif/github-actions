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
from jira import JIRA
from github import Github
import os
import sys
import json
from sync_pr import sync_remain_prs
from sync_issue import *
from push_event import handle_push_event


class _JIRA(JIRA):
    def applicationlinks(self):
        return []  # disable this function as we don't need it and it makes add_remote_links() slow


def main():
    if 'GITHUB_REPOSITORY' not in os.environ:
        print('Not running in GitHub action context, nothing to do')
        return

    if not os.environ['GITHUB_REPOSITORY'].startswith('espressif/'):
        print('Not an Espressif repo, nothing to sync to JIRA')
        return

    # Connect to Jira server
    print('Connecting to Jira Server...')
    jira = _JIRA(os.environ['JIRA_URL'],
                 basic_auth=(os.environ['JIRA_USER'],
                             os.environ['JIRA_PASS']))

    # Check if it's a cron job
    if os.environ.get('INPUT_CRON_JOB'):
        sync_remain_prs(jira)
        return

    # The path of the file with the complete webhook event payload. For example, /github/workflow/event.json.
    with open(os.environ['GITHUB_EVENT_PATH'], 'r') as f:
        event = json.load(f)
        print(json.dumps(event, indent=4))
    
    # Check if it's a push event
    if os.environ['GITHUB_EVENT_NAME'] == 'push':
        handle_push_event(event)
        return

    event_name = os.environ['GITHUB_EVENT_NAME']  # The name of the webhook event that triggered the workflow.
    action = event["action"]

    if event_name == 'pull_request':
        # Treat pull request events just like issues events for syncing purposes
        # (we can check the 'pull_request' key in the "issue" later to know if this is an issue or a PR)
        event_name = 'issues'
        event["issue"] = event["pull_request"]
        if "pull_request" not in event["issue"]:
            event["issue"]["pull_request"] = True  # we don't care about the value

    # don't sync if user is our collaborator
    github = Github(os.environ['GITHUB_TOKEN'])
    repo = github.get_repo(os.environ['GITHUB_REPOSITORY'])
    gh_issue = event["issue"]
    is_pr = "pull_request" in gh_issue
    if is_pr and repo.has_in_collaborators(gh_issue["user"]["login"]):
        print("Skipping issue sync for Pull Request from collaborator")
        return

    action_handlers = {
        'issues': {
            'opened': handle_issue_opened,
            'edited': handle_issue_edited,
            'closed': handle_issue_closed,
            'deleted': handle_issue_deleted,
            'reopened': handle_issue_reopened,
            'labeled': handle_issue_labeled,
            'unlabeled': handle_issue_unlabeled,
        },
        'issue_comment': {
            'created': handle_comment_created,
            'edited': handle_comment_edited,
            'deleted': handle_comment_deleted,
        },
    }

    if event_name not in action_handlers:
        print("No handler for event '%s'. Skipping." % event_name)
    elif action not in action_handlers[event_name]:
        print("No handler '%s' action '%s'. Skipping." % (event_name, action))
    else:
        action_handlers[event_name][action](jira, event)


if __name__ == "__main__":
    main()
