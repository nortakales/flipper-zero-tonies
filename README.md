# Toniebox NFC Files

This repo contains `.nfc` files to be used with Flipper Zero. Just place them in your `nfc` folder, and then emulate them.

## Directory

We have a directory of Tonies in this repo for each language:

* [English Tonies](English/README.md)
* [French Tonies](French/README.md)
* [German Tonies](German/README.md)

## Usage Notes

* Reading/emulating SLIX-L chips is a fairly new addition to the official Flipper Zero firmware.
  Keep that in mind if you are uploading your kid's cherished figures.

## Pull Requests

Pull requests are welcome!

If you want to add new Tonies, it will help to run `scripts/validate_files.sh` before opening a pull request.
If it detects something wrong with any of the files, it will tell you, and you can fix it before submitting the PR.
Otherwise, it will output no message at all.
It will also run when your PR is opened automatically.

You can use the `figures_name_tool.py` to generate the correct name for your file and place them in the correct directory.
To use this tool you need to have python installed and install all requirements with `pip install -r requirements.txt`