#!/bin/bash

shopt -s globstar

REQUIRED_PATTERNS=(
    "Filetype: Flipper NFC device"
    "Version: 4"
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

for filename in **/*.nfc; do

    for pattern in "${REQUIRED_PATTERNS[@]}"; do
        if [ -z "$(grep -P "$pattern" "$filename")" ]; then
            echo $filename
            echo "    Missing: $pattern"
        fi
    done

    # The likelihood of two blocks of 00 in data content is almsot impossible,
    # so use that as a check for when the full data is not read
    if [ ! -z "$(grep -P "Data Content:( [A-F0-9]{2})* 00 00( [A-F0-9]{2})*" "$filename")" ]; then
        echo $filename
        echo "    Full data not read"
    fi

done
