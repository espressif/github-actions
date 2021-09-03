#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2021 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

import json
import os
import shutil
import time

import gitlab
import requests
from git import Git, Repo


def pr_check_forbidden_files(pr_files_url):
    print("Checking if PR modified forbidden files...")
    # Requires Github Access Token, with Push Access
    GITHUB_TOKEN = os.environ['GITHUB_TOKEN']

    r = requests.get(pr_files_url, headers={'Authorization': 'token ' + GITHUB_TOKEN})
    r_data = r.json()

    pr_files = [file_info['filename'] for file_info in r_data
                if (file_info['filename']).find('.gitlab') != -1 or (file_info['filename']).find('.github') != -1]
    if pr_files:
        raise SystemError("PR modifying forbidden files!!!")


def pr_check_approver_access(project_users_url, pr_approver):
    print("Checking if PR approver access level matches criteria...")
    # Requires Github Access Token, with Push Access
    GITHUB_TOKEN = os.environ['GITHUB_TOKEN']

    # NOTE: General form is: https://api.github.com/repos/org/repo/collaborators{/collaborator}, hence stripping the end
    project_users_url = project_users_url.split('{/')[0]

    r = requests.get(project_users_url, headers={'Authorization': 'token ' + GITHUB_TOKEN})
    r_data = r.json()

    pr_appr_perm = [usr for usr in r_data if usr['login'] == pr_approver][0]['permissions']
    if not pr_appr_perm['triage']:
        raise SystemError("PR Approver Access is below TRIAGE level!")


def setup_project(project_fullname):
    print('Connecting to gitlab...')
    GITLAB_URL = os.environ['GITLAB_URL']
    GITLAB_TOKEN = os.environ['GITLAB_TOKEN']

    gl = gitlab.Gitlab(url=GITLAB_URL, private_token=GITLAB_TOKEN)
    gl.auth()

    HDR_LEN = 8
    gl_project_url = GITLAB_URL[: HDR_LEN] + GITLAB_TOKEN + ':' + GITLAB_TOKEN + '@' + GITLAB_URL[HDR_LEN :] + '/' + project_fullname + '.git'

    print(Git(".").clone(gl_project_url, recursive=True))
    return gl


def check_remote_branch(project, pr_branch):
    ret = None
    for x in range(0, 15):
        try:
            ret = project.branches.get(pr_branch)
        except Exception:
            time.sleep(1)
            pass

        if ret != None:
            return

    raise SystemError("PR branch creation failed!")


# Merge PRs with/without Rebase
def sync_pr(project_name, pr_num, pr_branch, project_html_url, pr_html_url, rebase_flag):
    GITHUB_REMOTE_NAME = 'github'
    GITHUB_REMOTE_URL = project_html_url

    HDR_LEN = 8
    GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
    gh_remote = GITHUB_REMOTE_URL[: HDR_LEN] + GITHUB_TOKEN + ':' + GITHUB_TOKEN + '@' + GITHUB_REMOTE_URL[HDR_LEN :]

    git = Git(project_name)

    print('Checking out to master branch...')
    print(git.checkout('master'))

    print('Adding the Github remote...')
    print(git.remote('add', GITHUB_REMOTE_NAME, gh_remote))

    print('Fetching the PR branch...')
    print(git.fetch(GITHUB_REMOTE_NAME, 'pull/' + str(pr_num) + '/head'))

    print('Checking out the PR branch...')
    print(git.checkout('FETCH_HEAD', b=pr_branch))

    if rebase_flag:
        #  Set the config parameters: Better be a espressif bot
        repo = Repo(project_name)
        repo.config_writer().set_value('user', 'name', os.environ['GIT_CONFIG_NAME']).release()
        repo.config_writer().set_value('user', 'email', os.environ['GIT_CONFIG_EMAIL']).release()

        print('Rebasing with the latest master...')
        print(git.rebase('master'))

        commit = repo.head.commit
        new_cmt_msg = commit.message + '\nMerges ' + pr_html_url

        print('Amending commit message (Adding additional info about commit)...')
        print(git.execute(['git','commit', '--amend', '-m', new_cmt_msg]))

    print('Pushing to remote...')
    print(git.push('--set-upstream', 'origin', pr_branch))


def main():
    if 'GITHUB_REPOSITORY' not in os.environ:
        print('Not running in GitHub action context, nothing to do')
        return

    if not os.environ['GITHUB_REPOSITORY'].startswith('espressif/'):
        print('Not an Espressif repo!')
        return

    # The path of the file with the complete webhook event payload. For example, /github/workflow/event.json.
    with open(os.environ['GITHUB_EVENT_PATH'], 'r') as f:
        event = json.load(f)
        # print(json.dumps(event, indent=4))

    event_name = os.environ['GITHUB_EVENT_NAME']  # The name of the webhook event that triggered the workflow.
    action = event["action"]
    state = event["review"]["state"]
    review_body = event["review"]["body"]

    if event_name != 'pull_request_review' or state != 'approved':
        raise SystemError("False Trigger!")

    pr_base = event["pull_request"]["base"]["ref"]
    if pr_base != 'master':
        raise SystemError("PR base illegal! Should be the master branch!")

    project_fullname = event["repository"]["full_name"]
    project_org, project_name = project_fullname.split("/")
    project_users_url = event["repository"]["collaborators_url"]
    project_html_url = event["repository"]["clone_url"]

    pr_num = event["pull_request"]["number"]
    pr_branch = 'contrib/github_pr_' + str(pr_num)
    pr_rest_url = event["pull_request"]["url"]
    pr_html_url = event["pull_request"]["html_url"]

    pr_files_url = pr_rest_url + '/files'
    # Check whether the PR has modified forbidden files
    pr_check_forbidden_files(pr_files_url)

    pr_approver = event["review"]["user"]["login"]
    # Checks whether the approver access level is above required; needs Github access token
    pr_check_approver_access(project_users_url, pr_approver)

    # Getting the PR title and body
    pr_title = event["pull_request"]["title"]
    idx = pr_title.find(os.environ['JIRA_PROJECT']) # Finding the JIRA issue tag
    pr_title_desc = pr_title[0 : idx - 2] # For space character
    pr_jira_issue = pr_title[idx : -1]
    pr_body = event["pull_request"]["body"]

    # Gitlab setup and cloning internal codebase
    gl = setup_project(project_fullname)

    if "/rebase" in review_body:
        sync_pr(project_name, pr_num, pr_branch, project_html_url, pr_html_url, rebase_flag=True)
    elif "/merge" in review_body:
        sync_pr(project_name, pr_num, pr_branch, project_html_url, pr_html_url, rebase_flag=False)
    else:
        print('No action selected!!!')
        return

    # Deleting local repo
    shutil.rmtree(project_name)

    print('Creating a merge request...')
    project_gl = gl.projects.get(project_fullname)

    # NOTE: Remote takes some time to register a branch
    time.sleep(15)
    # check_remote_branch(project_gl, pr_branch)

    mr = project_gl.mergerequests.create({'source_branch': pr_branch, 'target_branch': 'master', 'title': pr_title_desc})

    print('Updating merge request description...')
    mr_desc = pr_body + '\n #### (Add more info here)' + '\n## Related'
    mr_desc +=  '\n* Closes ' + pr_jira_issue
    mr_desc += '\n## Release notes (Mandatory)\n ### To-be-added'

    mr.description = mr_desc
    mr.save()

    print('Done with the merge request!')


if __name__ == '__main__':
    main()
