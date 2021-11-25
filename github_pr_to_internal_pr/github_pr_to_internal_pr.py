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


def pr_check_approver(pr_creator, pr_comments_url, pr_approve_labeller):
    print('Checking PR comment and affixed label...')
    # Requires Github Access Token, with Push Access
    GITHUB_TOKEN = os.environ['GITHUB_TOKEN']

    r = requests.get(pr_comments_url, headers={'Authorization': 'token ' + GITHUB_TOKEN})
    r_data = r.json()

    for comment in reversed(r_data):
        comment_body = comment['body']
        if comment_body.startswith('sha=') and comment['user']['login'] == pr_approve_labeller != pr_creator:
                return comment_body[4 : ]

    raise SystemError("PR Comment Error: Ensure that Command comment exists and PR commenter and labeller match!")


def pr_check_forbidden_files(pr_files_url):
    print('Checking if PR modified forbidden files...')
    # Requires Github Access Token, with Push Access
    GITHUB_TOKEN = os.environ['GITHUB_TOKEN']

    r = requests.get(pr_files_url, headers={'Authorization': 'token ' + GITHUB_TOKEN})
    r_data = r.json()

    pr_files = [file_info['filename'] for file_info in r_data
                if (file_info['filename']).find('.gitlab') != -1 or (file_info['filename']).find('.github') != -1]
    if pr_files:
        raise SystemError("PR modifying forbidden files!!!")


def get_github_remote(project_html_url):
    GITHUB_REMOTE_URL = project_html_url

    HDR_LEN = 8
    GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
    gh_remote = GITHUB_REMOTE_URL[: HDR_LEN] + GITHUB_TOKEN + ':' + GITHUB_TOKEN + '@' + GITHUB_REMOTE_URL[HDR_LEN :]

    return gh_remote


def setup_project(project_fullname):
    print('Connecting to GitLab...')
    GITLAB_URL = os.environ['GITLAB_URL']
    GITLAB_TOKEN = os.environ['GITLAB_TOKEN']

    gl = gitlab.Gitlab(url=GITLAB_URL, private_token=GITLAB_TOKEN)
    gl.auth()

    HDR_LEN = 8
    gl_project_url = GITLAB_URL[: HDR_LEN] + GITLAB_TOKEN + ':' + GITLAB_TOKEN + '@' + GITLAB_URL[HDR_LEN :] + '/' + project_fullname + '.git'

    Git(".").clone(gl_project_url, recursive=True)
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


def check_update_label(pr_label, pr_labels_list):
    LABEL_MERGE = 'PR-Sync-Merge'
    LABEL_REBASE = 'PR-Sync-Rebase'

    label_validity = [label['name'] for label in pr_labels_list
            if label['name'] == LABEL_MERGE or label['name'] == LABEL_REBASE]

    if not label_validity:
        raise SystemError('PR-Sync-Update Label: Illegal use!')


# Update existing MR
def update_mr(project_name, pr_num, pr_branch, pr_commit_id, project_html_url, project_gl):
    branch = project_gl.branches.get(pr_branch)
    if not branch:
        raise SystemError("PR Update: No branch found on internal remote to update!")

    GITHUB_REMOTE_NAME = 'github'
    gh_remote = get_github_remote(project_html_url)
    git = Git(project_name)

    print('Adding the Github remote...')
    git.remote('add', GITHUB_REMOTE_NAME, gh_remote)
    git.checkout(pr_branch)

    print('Checking out to master...')
    git.checkout('master')

    print('Updating the PR branch...')
    git.branch('--delete', pr_branch)
    git.fetch(GITHUB_REMOTE_NAME, 'pull/' + str(pr_num) + '/head')
    git.checkout('FETCH_HEAD', b=pr_branch)

    print('Checking whether specified commit ID matches with user branch HEAD...')
    expected_commit_id = git.rev_parse('--short', 'HEAD')

    if not pr_commit_id.startswith(expected_commit_id):
        raise SystemError("PR Commit SHA1 in workflow comment and user branch do not match!")

    print('Pushing to remote...')
    git.push('--force', 'origin', pr_branch)


# Merge PRs with/without Rebase
def sync_pr(project_name, pr_num, pr_branch, pr_commit_id, project_html_url, project_gl, pr_html_url, rebase_flag):
    branch = project_gl.branches.get(pr_branch)
    if branch:
        raise SystemError("PR Merge/Rebase: Branch/MR already exists for PR!")

    GITHUB_REMOTE_NAME = 'github'
    gh_remote = get_github_remote(project_html_url)

    git = Git(project_name)

    print('Checking out to master branch...')
    git.checkout('master')

    print('Adding the Github remote...')
    git.remote('add', GITHUB_REMOTE_NAME, gh_remote)

    print('Fetching the PR branch...')
    git.fetch(GITHUB_REMOTE_NAME, 'pull/' + str(pr_num) + '/head')

    print('Checking out the PR branch...')
    git.checkout('FETCH_HEAD', b=pr_branch)

    print('Checking whether specified commit ID matches with user branch HEAD...')
    expected_commit_id = git.rev_parse('--short', 'HEAD')

    if not pr_commit_id.startswith(expected_commit_id):
        raise SystemError("PR Commit SHA1 in workflow comment and user branch do not match!")

    if rebase_flag:
        #  Set the config parameters: Better be a espressif bot
        repo = Repo(project_name)
        repo.config_writer().set_value('user', 'name', os.environ['GIT_CONFIG_NAME']).release()
        repo.config_writer().set_value('user', 'email', os.environ['GIT_CONFIG_EMAIL']).release()

        print('Rebasing with the latest master...')
        git.rebase('master')

        commit = repo.head.commit
        new_cmt_msg = commit.message + '\nMerges ' + pr_html_url

        print('Amending commit message (Adding additional info about commit)...')
        git.execute(['git','commit', '--amend', '-m', new_cmt_msg])

    print('Pushing to remote...')
    git.push('--set-upstream', 'origin', pr_branch)


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

    LABEL_MERGE = 'PR-Sync-Merge'
    LABEL_REBASE = 'PR-Sync-Rebase'
    LABEL_UPDATE = 'PR-Sync-Update'

    pr_label = event['label']['name']
    pr_labels_list = event['pull_request']['labels']

    pr_approve_labeller = event['sender']['login']
    pr_creator = event['pull_request']['user']['login']
    pr_comments_url = event['pull_request']['comments_url']
    # Checks whether the approve labeller and workflow initiator are the same
    pr_commit_id = pr_check_approver(pr_creator, pr_comments_url, pr_approve_labeller)

    project_fullname = event['repository']['full_name']
    project_org, project_name = project_fullname.split('/')
    project_html_url = event['repository']['clone_url']

    pr_num = event['pull_request']['number']
    pr_branch = 'contrib/github_pr_' + str(pr_num)
    pr_rest_url = event['pull_request']['url']
    pr_html_url = event['pull_request']['html_url']

    pr_files_url = pr_rest_url + '/files'
    # Check whether the PR has modified forbidden files
    pr_check_forbidden_files(pr_files_url)

    # Getting the PR title and body
    pr_title = event['pull_request']['title']
    idx = pr_title.find(os.environ['JIRA_PROJECT'])  # Finding the JIRA issue tag
    pr_title_desc = pr_title[0 : idx - 2]  # For space character
    pr_jira_issue = pr_title[idx : -1]
    pr_body = event['pull_request']['body']

    # Gitlab setup and cloning internal codebase
    gl = setup_project(project_fullname)
    project_gl = gl.projects.get(project_fullname)

    if pr_label == LABEL_REBASE:
        sync_pr(project_name, pr_num, pr_branch, pr_commit_id, project_html_url, pr_html_url, rebase_flag=True)
    elif pr_label == LABEL_MERGE:
        sync_pr(project_name, pr_num, pr_branch, pr_commit_id, project_html_url, pr_html_url, rebase_flag=False)
    elif pr_label == LABEL_UPDATE:
        check_update_label(pr_label, pr_labels_list)
        update_mr(project_name, pr_num, pr_branch, pr_commit_id, project_html_url, project_gl)
        print('Done with the workflow!')
        return
    else:
        raise SystemError("Illegal program flow!")

    # Deleting local repo
    shutil.rmtree(project_name)

    # NOTE: Remote takes some time to register a branch
    time.sleep(15)

    print('Creating a merge request...')
    mr = project_gl.mergerequests.create({'source_branch': pr_branch, 'target_branch': 'master', 'title': pr_title_desc})

    print('Updating merge request description...')
    mr_desc = '## Description \n' + pr_body + '\n ##### (Add more info here)' + '\n## Related'
    mr_desc +=  '\n* Closes ' + pr_jira_issue
    mr_desc += '\n## Release notes (Mandatory)\n ### To-be-added'

    mr.description = mr_desc
    mr.save()

    print('Done with the merge request!')


if __name__ == '__main__':
    main()
