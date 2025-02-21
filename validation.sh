#!/usr/bin/env bash

ERR_FOUND=0

REQUIRED_PATTERNS=(
  "Filetype: Flipper NFC device"
  "Version: 4"
  "Device type: SLIX"
  "UID:( [A-F0-9]{2}){8}"
  "DSFID: 00"
  "AFI: 00"
  "IC Reference: 03"
  "Lock DSFID: false"
  "Lock AFI: false"
  "Block Count: 8"
  "Block Size: 04"
  "Data Content:( [A-F0-9]{2}){32}"
  "Security Status: 00 00 00 00 00 00 00 00"
  "Capabilities: Default"
  "Password Privacy: 7F FD 6E 5B"
  "Password Destroy: 0F 0F 0F 0F"
  "Password EAS: 00 00 00 00"
  "Privacy Mode: false"
  "Lock EAS: false"
)

FORBIDDEN_PATTERNS=(
  "Subtype: ([0-9]){2}"
  # Add more forbidden patterns here
)

# Use process substitution so that ERR_FOUND is updated in the main shell.
while read -r filename; do
  content=$(cat "$filename")

  for pattern in "${REQUIRED_PATTERNS[@]}"; do
    if ! echo "$content" | awk "/$pattern/ { found=1 } END { exit !found }"; then
      echo "$filename"
      echo "    Missing: $pattern"
      ERR_FOUND=1
    fi
  done

  # The likelihood of two blocks of 00 in data content is almost impossible,
  # so use that as a check for when the full data is not read
  if echo "$content" | awk '/Data Content:( [A-F0-9]{2})* 00 00( [A-F0-9]{2})*/ { found=1 } END { exit !found }'; then
    echo "$filename"
    echo "    Full data not read"
    ERR_FOUND=1
  fi

  if echo "$content" | awk '/\r/ { found=1 } END { exit !found }'; then
    echo "$filename"
    echo "    Has carriage return characters"
    ERR_FOUND=1
  fi

  for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
    if echo "$content" | awk "/$pattern/ { found=1 } END { exit !found }"; then
      echo "$filename"
      echo "    Forbidden pattern found: $pattern"
      ERR_FOUND=1
    fi
  done

done < <(find . -type f -name "*.nfc")

exit $ERR_FOUND
