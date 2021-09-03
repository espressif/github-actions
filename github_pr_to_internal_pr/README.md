# GitHub PR to Internal Codebase Sync

This script automates the process of creating branches and PRs on the internal codebase of Espressif based on approved PRs on Github.

## Flow

1. The action is triggered is when the approver (having an access level > [TRIAGE](https://docs.github.com/en/organizations/managing-access-to-your-organizations-repositories/repository-permission-levels-for-an-organization#permission-levels-for-repositories-owned-by-an-organization) in Github ESP-IDF) approves a PR with either '/rebase' or '/merge' in the approval comment.
2. If the approver does not include any of these commands in the approval comment, the workflow will be skipped.
3. The '/rebase' command will create an internal PR by rebasing the Github PR on the latest internal master (for old PRs).
4. The '/merge' command will create an internal PR by fetching the Github PR branch head and pushing it to the internal remote (for relatively new PRs)

## To-Do:

- [ ] Behaviour on two approvals with different approaches (rebase / merge) on the same PR

- [ ] Behaviour when PR contains multiple commits ([ref](https://github.com/espressif/github-actions/pull/17#discussion_r703454250))

- [ ] Handling of conflicts while using the rebase approach

- [ ] Find a better approach for `sleep(time)` as remote takes time to register a branch ([ref](https://github.com/espressif/github-actions/pull/17#discussion_r703455914))

- [ ] Generalize the default branch name, currently assumed "master"
