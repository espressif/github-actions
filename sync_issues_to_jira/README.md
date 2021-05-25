# GitHub to JIRA Issue Sync

This is a GitHub action that performs simple one way syncing of GitHub issues into JIRA.

* When a new GitHub issue is opened
  - A corresponding JIRA issue (in the configured JIRA project) is created.
  - Markdown in the GitHub issue body is converted into JIRA Wiki format (thanks to [markdown2confluence](http://chunpu.github.io/markdown2confluence/browser/))
  - A JIRA custom field "GitHub Reference" is set to the URL of the issue
  - The GitHub issue title has `(JIRA-KEY)` appended to it.
* When a GitHub issue is edited, the summary and description of the JIRA issue are updated.
* When comments are made on the GitHub issue, a comment is created on the JIRA issue.
* When GitHub comments are edited or deleted a comment is created on the JIRA issue.
* When the GitHub issue is closed or deleted a comment is created on the JIRA issue.
* When labels are added or removed from the GitHub issue, the same label is added or removed from the JIRA issue.

# 'Synced From' Link

After a synced JIRA issue is created, the action creates a [Remote Issue Link](https://developer.atlassian.com/server/jira/platform/creating-remote-issue-links/) on the JIRA issue, where the "[globalID](https://developer.atlassian.com/server/jira/platform/using-fields-in-remote-issue-links/#globalid)" is the GitHub issue URL.

This remote issue link is used to find existing synced issues when changes happen.

The sync action will continue to update JIRA issues which are moved to other JIRA projects, provided the remote issue link is moved and the Github Action's JIRA user can see the new project.

To break a link between a GitHub issue and a JIRA issue, delete the Remote Issue Link. (Note that if the GitHub Issue is updated later on, this action may create a new JIRA issue to track it.)

Note that manually created Remote Issue Links to GitHub issues will not have the globalID set, so they won't work (JIRA doesn't give a way to search for Remote Issue Links by URL, only by globalID, so there's no automated solution to this problem.)

# Manually Linking a GitHub Issue

It's not possible to create a Remote Issue Link with the correct `globalID` without using the JIRA API. Instead, to manually connect an existing GitHub issue with a JIRA issue in the Web UI:

1. Check that no other JIRA issue is syncing this GitHub issue (advanced search for `issue in issuesWithRemoteLinksByGlobalId("GitHub Issue URL")`).
2. Put the URL of the GitHub issue somewhere in the JIRA issue description.
3. Put the JIRA issue key at the end of the GitHub issue title, in parentheses. Like this: `GitHub Issue title (JIRAKEY-123)`

The GitHub action will create the "Synced from" link the next time this issue is updated (probably immediately, if you did the steps in the written order).

Important: If the URL of the GitHub issue is not found in the JIRA issue description, nothing will happen (this is to prevent external parties from making unintended updates to JIRA issues.)

# Issue Types

If a new GitHub issue has any labels where the name of the label matches the name of an issue type, or the name of the label matches `Type: <issue type>`, then the JIRA issue will be created with that issue type. Matching is case insensitive.

If no labels match issue types, environment variable `JIRA_ISSUE_TYPE` is used as the type for new issues. If `JIRA_ISSUE_TYPE` is not set, the default new issue type is "Task".

Changing labels on a GitHub issue does not change the issue type, because [JIRA REST API currently cannot safely change an issue type to one with a different workflow](https://jira.atlassian.com/browse/JRACLOUD-68207). Instead, an issue comment is left in JIRA.

# Limitations

Currently does not sync the following things:

* Labels, apart from any which match Issue Types
* Transitions. Closing, Reopening or Deleting an issue in GitHub only leaves a comment in the JIRA issue. This is at least partially by design because sometimes GitHub issues are closed by their reporters even though an underlying issue still needs fixing in the codebase.

# Usage

- [Sync a new issue to Jira](#sync-a-new-issue-to-jira)
- [Sync a new issue comment to Jira](#sync-a-new-issue-comment-to-jira)
- [Sync a new pull request to Jira](#sync-a-new-pull-request-to-jira)

## Sync a new issue to Jira

```yaml
name: Sync issues to Jira
# This workflow will be triggered when a new issue is opened
on: issues

jobs:
  sync_issues_to_jira:
    name: Sync issues to Jira
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@master
      - name: Sync GitHub issues to Jira project
        uses: espressif/github-actions/sync_issues_to_jira@master
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          JIRA_PASS: ${{ secrets.JIRA_PASS }}
          JIRA_PROJECT: SOMEPROJECT
          JIRA_COMPONENT: SOMECOMPONENT
          JIRA_URL: ${{ secrets.JIRA_URL }}
          JIRA_USER: ${{ secrets.JIRA_USER }}
```

## Sync a new issue comment to Jira

Syncing an issue comment works the same way. The only difference is the trigger event.

```yaml
name: Sync issue comments to JIRA
# This workflow will be triggered when new issue comment is created (including PR comments)
on: issue_comment
...
```

## Sync a new pull request to Jira

Actions for pull requests run with the privileges of the PR submitter's repo - for security reasons, as they can modify the contents of them.
If the action is run on the PR event, it can't access the necessary GH secrets containing Jira credentials.
Therefore PR syncing has to run as a cron task which is loaded from the master branch and run with all privileges.

```yaml
name: Sync remaining PRs to Jira
# This workflow will be triggered every hour to sync remaining PRs (i.e. PRs with zero comment) to Jira project
# Note that PRs can also get synced when a new PR comment is created
on:
  schedule:
    - cron: "0 * * * *"

jobs:
  sync_prs_to_jira:
    name: Sync PRs to Jira
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@master
      - name: Sync PRs to Jira project
        uses: espressif/github-actions/sync_issues_to_jira@master
        with:
          cron_job: true
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          JIRA_PASS: ${{ secrets.JIRA_PASS }}
          JIRA_PROJECT: SOMEPROJECT
          JIRA_COMPONENT: SOMECOMPONENT
          JIRA_URL: ${{ secrets.JIRA_URL }}
          JIRA_USER: ${{ secrets.JIRA_USER }}
```

# Variables

The environment variables should be set in the GitHub Workflow:

* `JIRA_PROJECT` is the slug of the JIRA project to create new issues in.
* `JIRA_ISSUE_TYPE` (optional) the JIRA issue type for new issues. If unset, "Task" is used.
* `JIRA_COMPONENT` (optional) the name of a JIRA component to add to every issue which is synced from GitHub. The component must already exist in the JIRA project.

The following secrets should be set in the workflow:

* `JIRA_URL` is the main JIRA URL (doesn't have to be secret).
* `JIRA_USER` is the JIRA username to log in with (JIRA basic auth)
* `JIRA_PASS` is the JIRA password to log in with (JIRA basic auth)

# Tests

test_sync_issue.py is a Python unittest framework that uses unittest.mock to create a mock JIRA API, then calls unit_test.py with various combinations of payloads similar to real GitHub Actions payloads.

The best way to run the tests is in the docker container, as this is the same environment that GitHub will run real actions in.

## Build image and run tests in a temporary container:

```
docker build . --tag jira-sync && docker run --rm --entrypoint=/test_sync_to_jira.py jira-sync
```

## Rebuild container and run tests multiple times

(This is a bit faster than rebuilding the image each time.)

Build the image and run the container once:

```
docker build . --tag jira-sync
docker run -td --name jira-sync --entrypoint=/bin/sh jira-sync
```

For each test run, copy the Python files to the running container and run the test program:

```
docker cp . jira-sync:/ && docker exec jira-sync /test_sync_to_jira.py
```

Once finished, kill the container:

```
docker stop -t1 jira-sync
```

## Cleanup

To clean up the container and container image:

```
docker rm jira-sync
docker rmi jira-sync
```
