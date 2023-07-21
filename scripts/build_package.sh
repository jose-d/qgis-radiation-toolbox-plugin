#!/bin/bash -e

find . -name __pycache__ | xargs rm -rf
pb_tool zip

exit 0
