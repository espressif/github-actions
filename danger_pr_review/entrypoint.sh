#!/bin/sh -l

# Copy the whole dangerjs directory to the workspace directory
cp -r /dangerjs/* /github/workspace

# Change to the workspace directory
cd /github/workspace || exit

# Run DangerJS
npx danger ci --failOnErrors -v
