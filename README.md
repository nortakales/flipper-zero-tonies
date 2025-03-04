# Toniebox NFC Files

This repo contains `.nfc` files to be used with Flipper Zero. Just place them in your `nfc` folder, and then emulate them.

## Directory

We have a directory of Tonies in this repo for each language:

* [English Tonies](English/README.md)
* [French Tonies](French/README.md)
* [German Tonies](German/README.md)

## Usage Notes

* Reading/emulating SLIX-L chips is a fairly new addition to the official Flipper Zero firmware.
  It disappeared for a few releases and came back as of `0.99.1` (with a different file format), so make sure you are on that version or newer.
* I'm not sure about unofficial firmwares and which versions support this, but I imagine it is supported by most.
* The Tonie Box downloads the audio data from servers, so it is possible that the data in this repo no longer works at some point.
  Keep that in mind if you are uploading your kid's cherished figures.

## Pull Requests

Pull requests are welcome!

If you want to add new Tonies, it will help to run `validation.sh` before opening a pull request.
If it detects something wrong with any of the files, it will tell you, and you can fix it before submitting the PR.
Otherwise, it will output no message at all.
It will also run when your PR is opened automatically.