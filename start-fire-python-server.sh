#!/bin/bash

# Bash script to start Python ISMRMRD server
#
# First argument is path to log file.  If no argument is provided,
# logging is done to stdout (and discarded)

# Set Python's default temp folder to one that's shared with the host so that
# it's less likely to accidentally fill up the chroot

docker run --rm -it -p 9002:9002 -v ./save:/opt/code/python-fire-server-base/save -v ./logs:/opt/code/python-fire-server-base/logs python-fire-server:base