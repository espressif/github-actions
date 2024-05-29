:warning: **Deprecation Notice**: This GitHub action is deprecated and development will not continue here. We recommend migrating to the latest version available in the [espressif/update-submodule-versions-action](https://github.com/espressif/update-submodule-versions-action) project.

---
# Update repository submodules action

This action helps automate updates to submodules of a repository. It is similar to Dependabot's submodule update functionality, with a few extra features:

1. Configuration of this action, specific to each submodule, is stored along with the rest of submodule information in `.gitmodules` file.
2. The action updates the submodule to the latest tag matching a certain pattern on a given branch.
3. The action can optionally update idf_component.yml file to the version matching the upstream version.

## Configuration

This action reads configuration from custom options in `.gitmodules` file. Here is an example:
```
[submodule "fmt/fmt"]
	path = fmt/fmt
	url = https://github.com/fmtlib/fmt.git
	autoupdate = true
	autoupdate-branch = master
	autoupdate-tag-glob = [0-9]*.[0-9]*.[0-9]*
	autoupdate-include-lightweight = true
	autoupdate-manifest = fmt/idf_component.yml
	autoupdate-ver-regex = ([0-9]+).([0-9]+).([0-9]+)
```


| Option                         | Possible values                 | Default | Explanation                                                                                                                 |
|--------------------------------|---------------------------------|---------|-----------------------------------------------------------------------------------------------------------------------------|
| autoupdate                     | `true`, `false`                 | `false` | Whether to update this submodule or not                                                                                     |
| autoupdate-branch              | string                          |         | Name of the submodule branch where to look for the new tags. Required if autoupdate=true.                                   |
| autoupdate-tag-glob            | Git glob expression             |         | Glob pattern (as used by 'git describe --match') to use when looking for tags. Required if autoupdate=true.                 |
| autoupdate-include-lightweight | `true`, `false`                 | `false` | Whether to include lightweight (not annotated) tags.                                                                        |
| autoupdate-manifest            | path relative to Git repository |         | If specified, sets the name of the idf_component.yml file where the version should be updated.                              |
| autoupdate-ver-regex           | regular expression              |         | Regular expression to extract major, minor, patch version numbers from the Git tag. Required if autoupdate-manifest is set. |

