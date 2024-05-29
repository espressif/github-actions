:warning: **Deprecation Notice**: This repository has been split into individual repositories—each GitHub action in its own repository—to achieve a cleaner development process, code ownership, and proper versioning.

GitHub actions from this repo will probably still work for some time, but development continues in the new locations. **This repo is now archived and read-only.**  :warning: 

---

:exclamation: **We strongly suggest updating your GitHub workflows to use the new repository locations.** By doing this, you can ensure you are using the proper versions of these actions with all the latest fixes and improvements.

| GitHub action               | migrated to new location                                      |
| --------------------------- | ------------------------------------------------------------- |
| `danger_pr_review`          | https://github.com/espressif/shared-github-dangerjs           |
| `github_pr_to_internal_pr`  | https://github.com/espressif/sync-pr-to-gitlab                |
| `release_zips`              | -                                                             |
| `sync_issues_to_jira`       | https://github.com/espressif/sync-jira-actions                |
| `update_submodule_versions` | https://github.com/espressif/update-submodule-versions-action |
| `upload_components`         | https://github.com/espressif/upload-components-ci-action      |

---

# Espressif Github Actions

[Github Actions](https://developer.github.com/actions/) developed by Espressif to help manage GitHub repositories.

- [sync_issues_to_jira](sync_issues_to_jira/) performs one-way syncing of GitHub issues into a JIRA project.
- [release_zips](release_zips/) creates a zip file from a tagged version to attach to a release (recursive clone, unlike the automatic GitHub source archives.)
- [upload_components](upload_components/) Uploads components from a GitHub repo to [Espressif Component Service](https://components.espressif.com)
- [github_pr_to_internal_pr](github_pr_to_internal_pr/) performs a sync of approved pull requests to Espressif's internal IDF integration.
- [danger_pr_review](danger_pr_review/) performs automatic style checking of pull requests using the DangerJS framework.

## Support and Changes

- Raising issues and sending Pull Requests is very welcome **in new GitHub action locations** (see the table above).
- However, please remember that some actions serve Espressif's internal GitHub integration needs. Issues or Pull Requests which aren't useful for those needs may not be addressed or merged. Sorry.

## License

Apache License 2.0
