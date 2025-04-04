#!/bin/sh
# Run the command passed in ${@} in a new mount & user namespace, with
# a tmpfs mounted at /var/run. This lets watchdogd create its socket
# and other files in /var/run without real root access and without
# interfering with system services.
if [ -z "${PWDOG_TEST_NS}" ]; then
    export PWDOG_TEST_NS=1
    exec unshare -r -m "${0}" "${@}"
elif [ "${PWDOG_TEST_NS}" = "1" ]; then
    mount -t tmpfs tmpfs "$(realpath /var/run)"
    exec "${@}"
else
    exit 2
fi
