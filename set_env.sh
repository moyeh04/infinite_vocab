#!/usr/bin/env bash

# Script to set environment variables for the Infinite Vocab backend.

# Usage:
#   source ./set_env.sh			 # Default: Configure for Firebase Emulators
#   source ./set_env.sh local    # Explicitly configure for Emulators
#   source ./set_env.sh cloud    # Configure for LIVE Firebase Cloud project

# --- Configuration ---
SERVICE_ACCOUNT_FILE="serviceAccountKey.json"

# --- Set Static Exports ---
export GCLOUD_PROJECT="infinite-vocab" # Set project ID explicitly

# IMPORTANT: serviceAccountKey.json should be in .gitignore and NEVER committed!
INFINITE_SECURITY="$(pwd)/${SERVICE_ACCOUNT_FILE}"
export INFINITE_SECURITY

# --- Determine Mode ---
MODE=${1:-local} # Default to 'local' (emulator) if no argument $1 is provided

# --- Initialize Message Variables ---
MSG_MODE="Setting environment for: $MODE"
MSG_PROJECT="Exporting GCLOUD project ID: $GCLOUD_PROJECT"
MSG_WARNING=""
MSG_CREDENTIAL=""
MSG_CONFIG=""
MSG_EMULATORS=""
MSG_FINAL="Environment set."

# --- Check Credentials File ---
if [ -f "$INFINITE_SECURITY" ]; then
	MSG_CREDENTIAL="Exporting INFINITE_SECURITY: $INFINITE_SECURITY"
else
	MSG_WARNING="Warning: Service account key not found at $INFINITE_SECURITY\n         Firebase initialization WILL FAIL."
fi

# --- Mode-Specific Settings ---
case "$MODE" in
cloud)
	# --- Cloud Mode ---
	MSG_CONFIG="Configuring for LIVE Firebase Cloud."
	# Ensure emulator hosts are NOT set

	unset FIREBASE_AUTH_EMULATOR_HOST
	unset FIRESTORE_EMULATOR_HOST
	;; # End of 'cloud' case

local)
	# --- Emulator (Local) Mode ---
	MSG_CONFIG="Configuring for Firebase Emulators."
	# Set emulator hosts
	export FIREBASE_AUTH_EMULATOR_HOST="localhost:9099"
	export FIRESTORE_EMULATOR_HOST="localhost:8080"
	MSG_EMULATORS=$(
		cat <<EMULATOR_EOF
-> Exporting FIREBASE_AUTH_EMULATOR_HOST=$FIREBASE_AUTH_EMULATOR_HOST
-> Exporting FIRESTORE_EMULATOR_HOST=$FIRESTORE_EMULATOR_HOST
(NOTE: SDK will prioritize Emulators because *_EMULATOR_HOST variables are set)
EMULATOR_EOF
	)
	;; # End of 'local' case

*) # Matches any other input
	MSG_CONFIG="Error: Invalid mode '$MODE'."
	MSG_FINAL="Usage: source $0 [local|cloud]"
	echo -e "\nError: Invalid mode '$MODE'. Usage: source $0 [local|cloud]\n" >&2
	return 1
	;;  # End of default case
esac # End the case statement

# --- Print Combined Output ---
cat <<EOF
--------------------------------------------------
$MSG_MODE
$MSG_PROJECT
$MSG_CONFIG
$MSG_EMULATORS
$MSG_CREDENTIAL
$MSG_WARNING

$MSG_FINAL
--------------------------------------------------
EOF

# If return 1 was hit above, this part isn't reached when sourced
# If successful, return 0 explicitly
return 0
