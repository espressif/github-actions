#!/bin/bash

set -euo pipefail

git config --global --add safe.directory "*"

/usr/local/bin/python3 /update_submodule_versions.py \
  --repo "${GITHUB_WORKSPACE}" \
  --open-github-pr-in "${GITHUB_REPOSITORY}" \



