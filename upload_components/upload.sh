#!/bin/bash

function check_if_exists {
    EXIT_CODE=$?
    # Exit code 144 is returned when remote entity is already existed.
    if [ "$EXIT_CODE" -eq "0" ]; then
        return 0
    fi

    if [ "$EXIT_CODE" -eq "144" ]; then
        echo "Already exists! Skipping..."
        return 0
    fi

    echo "An error occurred while handling $ITEM"
    exit 1
}

IFS=';' read -ra DIRECTORIES <<<"${COMPONENTS_DIRECTORIES:-.}"
NAMESPACE=${COMPONENTS_NAMESPACE:-espressif}
if [ -n "$SKIP_PRE_RELEASE" ]; then
    SKIP_PRE_RELEASE_FLAG="--skip-pre-release"
fi

NUMBER_OF_DIRECTORIES="${#DIRECTORIES[@]}"
echo "Processing $NUMBER_OF_DIRECTORIES components"

for ITEM in "${DIRECTORIES[@]}"; do
    FULL_PATH="${GITHUB_WORKSPACE?}/${ITEM}"
    if [ "$NUMBER_OF_DIRECTORIES" -eq "1" ]; then
        NAME=${COMPONENT_NAME?}
    else
        NAME=$(basename "$(realpath "${FULL_PATH}")")
    fi

    echo "Creating namespace ${NAMESPACE}"
    python3 -m idf_component_manager create-remote-namespace \
        --namespace="${NAMESPACE}"

    check_if_exists

    echo "Creating component ${NAME}"
    python3 -m idf_component_manager create-remote-component \
        --namespace="${NAMESPACE}" \
        --name="${NAME}"

    check_if_exists

    echo "Processing component \"$NAME\" at $ITEM"
    python3 -m idf_component_manager upload-component \
        --path="${FULL_PATH}" \
        --namespace="${NAMESPACE}" \
        --name="${NAME}" \
        ${SKIP_PRE_RELEASE_FLAG}

    check_if_exists
done
