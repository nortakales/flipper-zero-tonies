
This repo contains `.nfc` files to be used with Flipper Zero. Just place them in your `nfc` folder, and then emulate them.

Pull requests welcome!

**Usage Notes**

*  Reading/emulating SLIX-L chips is a fairly new addition to the official Flipper Zero firmware. It disappeared for a few releases and came back as of `0.99.1` (with a different file format), so make sure you are on that version or newer. I'm not sure about unofficial firmwares and which versions support this yet.
* The Tonie Box downloads the audio data from servers, so it is possible that the data in this repo no longer works at some point. Keep that in mind if you are uploading your kid's cherished figures.

**Pull Requests**

If you want to add new Tonies, it will help to run `validation.sh`. If it detects something wrong with any of the files, it will tell you, and you can fix it before submitting the PR. Otherwise it will output no message at all. I will also run this from time to time and clean up files as needed.

You can use the `figures_name_tool.py` to generate the correct name for your file and place them in the correct directory.
To use this tool you need to have python installed and install all requirements with `pip install -r requirements.txt`