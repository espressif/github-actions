#!/bin/bash

IFS=';' read -ra DIRECTORIES <<<"${COMPONENTS_DIRECTORIES:-.}"
NAMESPACE=${COMPONENTS_NAMESPACE:-espressif}
if [ -n "$SKIP_PRE_RELEASE" ]; then
    SKIP_PRE_RELEASE_FLAG="--skip-pre-release"
fi

if [ -n "$COMPONENT_VERSION" ]; then
    if [ "$COMPONENT_VERSION" == "git" ]; then
        git fetch --force --tags
        if ! git describe --exact-match; then
            echo "Version is set to 'git', but the current commit is not tagged. Skipping the upload."
            exit 0
        fi
    fi
    COMPONENT_VERSION_OPTION="--version=${COMPONENT_VERSION}"
fi

NUMBER_OF_DIRECTORIES="${#DIRECTORIES[@]}"
echo "Processing $NUMBER_OF_DIRECTORIES components"

for ITEM in "${DIRECTORIES[@]}"; do
    FULL_PATH="${GITHUB_WORKSPACE?}/${ITEM}"
    if [ "$NUMBER_OF_DIRECTORIES" -eq "1" ] && [ "${ITEM}" == "." ] && [ -z "${COMPONENT_NAME}" ]; then
        echo "To upload a single component, either specify the component name or directory, which will be used as the component name"
        exit 1
    fi

    if [ "${ITEM}" == "." ]; then
        NAME=${COMPONENT_NAME?"Name is required to upload a component from the root of the repository."}
    else
        NAME=$(basename "$(realpath "${FULL_PATH}")")
    fi

    echo "Processing component \"$NAME\" at $ITEM"
    python3 -m idf_component_manager upload-component \
        --allow-existing \
        --path="${FULL_PATH}" \
        --namespace="${NAMESPACE}" \
        --name="${NAME}" \
        ${COMPONENT_VERSION_OPTION:-} \
        ${SKIP_PRE_RELEASE_FLAG:-}

    EXIT_CODE=$?
    if [ "$EXIT_CODE" -ne "0" ]; then
        echo "An error occurred while uploading the new version of ${NAMESPACE}/${NAME}."
        exit 1
    fi
done
