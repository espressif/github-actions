# GitHub Action to upload ESP-IDF components to the component registry

This action uploads [ESP-IDF](https://github.com/espressif/esp-idf) components from a GitHub repository to [Espressif Component Registry](https://components.espressif.com).

## Usage

The action requires `api_token` and `namespace` parameters to be set. If the repository contains the only component stored in the root of the repository, then the `name` parameter is also required. If the repository contains more than 1 component in subdirectories, it's necessary to set the `directories` parameter to the semicolon-separated list of directories with components. In this case, the base name of the directory will be used as a component name.

### Handling versions

If the version in the manifest file is not in the registry yet this action will upload it. Every version of the component can be uploaded to the registry only once.

It's recommended to change the version in the manifest only when it's ready to be published.
An alternative supported workflow is to set parameter `skip_pre_release` to any non-empty string and use [pre-release](https://semver.org/#spec-item-9) versions (like `1.0.0-dev`) during development and then change the version to a stable (like `1.0.0`) for release.

If the version of the component is not specified in the manifest file, you can use the `version` parameter. It must be a valid [semantic version](https://semver.org/) optionally prefixed with character "v". I.e. versions formatted like `v1.2.3` or `1.2.3` are supported.

If the component with the same version is already in the registry the action will skip uploading silently.

### Example workflows

#### Uploading one component with version from git tag

To upload components only on tagged commits add on-push-tags rule to the workflow and set `version` input to `${{ github.ref_name }}`.

```yaml
name: Push component to https://components.espressif.com
on:
  push:
    tags:
      - v*
jobs:
  upload_components:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
        with:
          submodules: "recursive"

      - name: Upload component to the component registry
        uses: espressif/github-actions/upload_components@master
        with:
          name: "my_component"
          version: ${{ github.ref_name }}
          namespace: "espressif"
          api_token: ${{ secrets.IDF_COMPONENT_API_TOKEN }}
```

#### Uploading multiple components from one repository

```yaml
name: Push components to https://components.espressif.com
on:
  push:
    branches:
      - main
jobs:
  upload_components:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
        with:
          submodules: "recursive"

      - name: Upload components to the component registry
        uses: espressif/github-actions/upload_components@master
        with:
          directories: "components/my_component;components/another_component"
          namespace: "espressif"
          api_token: ${{ secrets.IDF_COMPONENT_API_TOKEN }}
```

## Parameters

| Input            | Optional | Default   | Description                                                                                                                    |
| ---------------- | -------- | --------- | ------------------------------------------------------------------------------------------------------------------------------ |
| api_token        | ❌       |           | API Token for the component registry                                                                                           |
| namespace        | ❌       |           | Component namespace                                                                                                            |
| name             | ✔ / ❌   |           | Name is required for uploading a component from the root of the repository                                                     |
| version          | ✔        |           | Version of the component, if not specified in the manifest. Should be a [semver](https://semver.org/) like `1.2.3` or `v1.2.3` |
| directories      | ✔        | Repo root | Semicolon separated list of directories with components.                                                                       |
| skip_pre_release | ✔        | False     | Flag to skip [pre-release](https://semver.org/#spec-item-9) versions                                                           |
| service_url      | ✔        |           | API Endpoint, default https://api.components.espressif.com/                                                                    |
