# Sync approved PRs to internal codebase

This script automates the process of creating branches and PRs on the internal codebase of Espressif based on approved PRs on Github.

## Flow

1. When the PR is ready to merge after reviewing, the user needs to add a comment on the PR of the type `sha=1a2b3c4` where `sha` specifies the *SHA1 hash* (long or short) of the **most recent** commit to be merged/updated.
2. The PR is then affixed with a label `PR-Sync-Merge`, `PR-Sync-Rebase` or `PR-Sync-Update`, triggering the action of syncing the PR. (Labels can only be affixed by a user with an access level > [TRIAGE](https://docs.github.com/en/organizations/managing-access-to-your-organizations-repositories/repository-permission-levels-for-an-organization#permission-levels-for-repositories-owned-by-an-organization) in Github)
3. The `PR-Sync-Merge` label will create an internal PR by fetching the Github PR branch head and pushing it to the internal remote (for new PRs - close to the current `master` branch). This should be the preferred strategy while syncing.
4. The `PR-Sync-Rebase` label will create an internal PR by rebasing the Github PR on the latest internal master (for old PRs).
5. The `PR-Sync-Update` label will update the internal PR with new commits/changes on the PR fork branch. For triggering the update workflow after it has been already run once, remove and re-affix the `PR-Sync-Update` label.

## To-Do:

- [ ] Behaviour when PR contains multiple commits ([ref](https://github.com/espressif/github-actions/pull/17#discussion_r703454250))

- [ ] Handling of conflicts while using the rebase approach
