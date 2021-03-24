# Release zips

If you need to distribute source zip files containing a recursively cloned working directory of your repo (such as we do for ESP-IDF), then this action can automatically create one and attach it to a draft release whenever a matching tag is pushed.

The difference between this zip file and the automatic zip file that GitHub allows you to download from any tag or release is:

* This zip file is a recursive clone that includes all submodules.
* This zip file is a valid Git working directory

## Creating a Release

If a Release already exists for the given tag, then the zip file is attached to it. Otherwise, a placeholder Draft release is created and the zip file is attached to that.

If the tag contains `-` then a new Draft is marked as Pre-release and this is also mentioned in the title. The naming scheme for a new draft is based on ESP-IDF, and is `$RELEASE_PROJECT_NAME [Pre-release|Release] $TAG`. Both these things can be edited before publishing the new release.

## Example Workflow yaml file

```yml
name: Create recursive zip file for release

on:
  push:
    tags:
      - v*

jobs:
  release_zips:
    name: Create release zip files
    runs-on: ubuntu-20.04
    steps:
      - name: Create a recursive clone source zip for a Release
        uses: espressif/github-actions/release_zips@master
        env:
            RELEASE_PROJECT_NAME: ESP-IDF
            GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

* Note the `tags` filter for `push`, this limits the tag patterns for which a zip file should be created.
* `RELEASE_PROJECT_NAME` is the name that will be used in the Draft Release title, of the form "$RELEASE_PROJECT_NAME [Pre-release|Release] $TAG"
* `GITHUB_TOKEN` is needed to create the release, and used as a credential when cloning from GitHub (just in case). The token is not stored in the working directory, though.
