#!/usr/bin/env bash
# Browser stand-in. Python's webbrowser.open() honours $BROWSER, so pointing
# $BROWSER at this script records whether the framework tried to open a window
# — without patching, shimming or monkey-patching a single line of framework
# code. Pure black-box observation.
echo "BROWSER_OPENED: $*" >> "${BROWSER_LOG:-/dev/stderr}"
