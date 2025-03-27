import _libwdog  # type: ignore
import errno
import os


def ping() -> bool:
    """Check if watchdogd is reachable, return True if yes."""
    return _libwdog.lib.wdog_ping() == 0


class WdogStateException(Exception):
    pass


class Wdog:
    def __init__(self, label: str | bytes | None):
        """Create a watchdogd supervisor client with the given client
        label, which may appear in watchdogd logs. The client must
        subscribe before watchdogd will supervise it.

        If a subscribed client missed the timeout to pet the watchdog,
        watchdogd will restart the system or call a supervisor script,
        depending on its configuration.

        """
        # buffer for the latest ack value
        self._ack = _libwdog.ffi.new('unsigned int[1]')
        # current subscription ID if subscribed, otherwise None
        self._id: int | None = None
        # Used to track the configured timeout in ms, only valid while
        # subscribed.
        self._timeout = 0

        if isinstance(label, bytes):
            self.clabel = _libwdog.ffi.new('char[]', label)
        elif isinstance(label, str):
            self.clabel = _libwdog.ffi.new('char[]', label.encode())
        elif label is None:
            self.clabel = _libwdog.ffi.NULL
        else:
            raise TypeError('label must be a str or None')

    def _handle_error(self) -> None:
        """If watchdogd doesn't know the subscription ID (which should
        only happen if it was restarted), try to
        re-subscribe. Otherwise raise the appropriate exception.

        """
        err = _libwdog.ffi.errno
        if err == errno.EIDRM:
            self._id = None
            self.subscribe(self._timeout)
        else:
            raise OSError(err, os.strerror(err))

    def subscribe(self, timeout: int | float) -> None:
        """Subscribe to the watchdogd supervisor, with the given
        timeout in seconds."""
        if self._id is not None:
            raise WdogStateException('already subscribed')
        self._timeout = int(timeout * 1000)
        self._id = _libwdog.lib.wdog_subscribe(
            self.clabel, self._timeout, self._ack)
        if self._id < 0:
            err = _libwdog.ffi.errno
            self._id = None
            if err == errno.EINVAL:
                raise ValueError('invalid timeout')
            else:
                raise OSError(err, os.strerror(err))

    def unsubscribe(self) -> None:
        """Unsubscribe from the watchdog. After this watchdogd does
        not require regular pets."""
        if self._id is None:
            raise WdogStateException('not subscribed')
        ret = _libwdog.lib.wdog_unsubscribe(self._id, self._ack[0])
        if ret < 0:
            err = _libwdog.ffi.errno
            raise OSError(err, os.strerror(err))
        self._id = None

    def pet(self) -> None:
        """Pet the watchdog. This must be called at least once within
        timeout, calculated from subscription (at the start) or
        previous pet.

        """
        if self._id is None:
            raise WdogStateException('not subscribed')
        ret = _libwdog.lib.wdog_kick2(self._id, self._ack)
        if ret < 0:
            self._handle_error()
            self.pet()

    def set_timeout(self, timeout: int | float):
        """Pet the watchdog and change the configured timeout. New
        timeout is in seconds."""
        if self._id is None:
            raise WdogStateException('not subscribed')
        self._timeout = int(timeout * 1000)
        ret = _libwdog.lib.wdog_extend_kick(self._id, self._timeout, self._ack)
        if ret < 0:
            self._handle_error()
            self.set_timeout(timeout)
