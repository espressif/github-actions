# GitHub Action to upload ESP-IDF components to the component service

This action uploads [ESP-IDF](https://github.com/espressif/esp-idf) components from a GitHub repository to [Espressif Component Service](https://components.espressif.com).

## Usage

The action requires `api_token` and `namespace` parameters to be set. If the repository contains the only component stored in the root of the repository, then the `name` parameter is also required. If the repository contains more than 1 component in subdirectories, it's necessary to set the `directories` parameter to the semicolon-separated list of directories with components. In this case, the base name of the directory will be used as a component name.

For successful upload, a component should be created in advance, for example using `idf.py create-remote-component` command.

### Handling versions

If the version in the manifest file is not on the service yet this action will upload it. Every version of the component can be uploaded to the service only once.

It's recommended to change the version in the manifest only when it's ready to be published.
An alternative supported workflow is to set parameter `skip_pre_release` to any non-empty string and use [pre-release](https://semver.org/#spec-item-9) versions (like `1.0.0-dev`) during development and then change the version to a stable (like `1.0.0`) for release.

If the component with the same version is already on the service the action will ignore it silently.

### Example workflow

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
      - uses: actions/checkout@master
        with:
          submodules: "recursive"

      - name: Upload components to the component service
        uses: espressif/github-actions/upload_components@master
        with:
          directories: "components/my_component;components/another_component"
          namespace: "espressif"
          api_token: ${{ secrets.IDF_COMPONENT_API_TOKEN }}
```

## Parameters

| Input            | Optional | Default   | Description                                                          |
| ---------------- | -------- | --------- | -------------------------------------------------------------------- |
| api_token        | ❌       |           | API Token for component service                                      |
| namespace        | ❌       |           | Component namespace                                                  |
| name             | ✔ / ❌   |           | Name of the component, required if only 1 directory is set           |
| directories      | ✔        | Repo root | Semicolon separated list of directories with components              |
| service_url      | ✔        |           | API Endpoint                                                         |
| skip_pre_release | ✔        | False     | Flag to skip [pre-release](https://semver.org/#spec-item-9) versions |
