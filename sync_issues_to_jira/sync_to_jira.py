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
import warnings
warnings.simplefilter('default', DeprecationWarning)
warnings.warn(
    "You are using a deprecated version of the Jira sync GitHub action. "
    "We recommend migrating to the latest version available at https://github.com/espressif/sync-jira-actions.",
    DeprecationWarning
)

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

    # Check if the JIRA_PASS is token or password
    token_or_pass = os.environ['JIRA_PASS']
    if token_or_pass.startswith('token:'):
        print("Authenticating with JIRA_TOKEN ...")
        token = token_or_pass[6:]  # Strip the 'token:' prefix
        jira = _JIRA(os.environ['JIRA_URL'], token_auth=token)
    else:
        print("Authenticating with JIRA_USER and JIRA_PASS ...")
        jira = _JIRA(os.environ['JIRA_URL'], basic_auth=(os.environ['JIRA_USER'], token_or_pass))

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

    event_name = os.environ['GITHUB_EVENT_NAME']

    # Check if event is workflow_dispatch and action is mirror issues. If so, run manual mirroring and skip rest of the script. Works both for issues and pull requests.
    if event_name == 'workflow_dispatch':
        inputs = event.get('inputs')

        if not inputs:
            print('Triggered workflow_dispatch event without correct inputs. Exiting...')
            return

        input_action = inputs.get('action')
        issue_numbers = inputs.get('issue-numbers')
        if input_action != 'mirror-issues':
            print('This action needs input "mirror-issues". Exiting...')
            return
        if not issue_numbers:
            print('This action needs inputs "issue-numbers". Exiting...')
            return

        print(f'Starting manual sync of issues: {issue_numbers}')
        sync_issues_manually(jira, event)
        return

    # The name of the webhook event that triggered the workflow.
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
