#!/bin/bash

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

    echo "Processing component \"$NAME\" at $ITEM"
    python3 -m idf_component_manager upload-component \
        --path="${FULL_PATH}" \
        --namespace="${NAMESPACE}" \
        --name="${NAME}" \
        ${SKIP_PRE_RELEASE_FLAG}

    EXIT_CODE=$?
    # Exit code 144 is returned when component is already uploaded
    if [ "$EXIT_CODE" -ne "0" ] && [ "$EXIT_CODE" -ne "144" ]; then
        echo "An error occurred while uploading the new version of ${NAMESPACE}/${NAME}."
        exit 1
    fi
done
