# upload-wetransfer

Upload files or folders to WeTransfer

## Requirements

upload-wetransfer depends on [`python-requests`](https://github.com/kennethreitz/requests) and [`requests-toolbelt`](https://github.com/sigmavirus24/requests-toolbelt). You can install these requirements with `pip install requests requests-toolbelt`

## Usage

You can send one or several files at once, to one or several contacts. When uploading a directory, you can use the `-R` flag to activate recursive listing.

```usage: upload-wetransfer.py [-h] [-r [RECEIVER [RECEIVER ...]]] [-s SENDER]
                            [-m MESSAGE] [-R]
                            files [files ...]```
