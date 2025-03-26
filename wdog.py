import _libwdog
import os


def ping() -> bool:
    i = _libwdog.lib.wdog_ping()
    return i == 0


class WdogStateException(Exception):
    pass


class Wdog:
    def __init__(self, label: str | bytes):
        self._ack = _libwdog.ffi.new('unsigned int[1]')
        self._id: int | None = None
        if isinstance(label, bytes):
            self.clabel = _libwdog.ffi.new('char[]', label)
        elif isinstance(label, str):
            self.clabel = _libwdog.ffi.new('char[]', label.encode())
        elif label is None:
            self.clabel = _libwdog.ffi.NULL
        else:
            raise TypeError('label must be a str or None')

    def ping(self) -> bool:
        return ping()

    def subscribe(self, timeout: int) -> None:
        if self._id is not None:
            raise WdogStateException('already subscribed')
        self._id = _libwdog.lib.wdog_subscribe(self.clabel, timeout, self._ack)
        if self._id < 0:
            err = _libwdog.ffi.errno
            self._id = None
            raise OSError(err, os.strerror(err))

    def unsubscribe(self) -> None:
        if self._id is None:
            raise WdogStateException('not subscribed')
        ret = _libwdog.lib.wdog_unsubscribe(self._id, self._ack[0])
        if ret < 0:
            err = _libwdog.ffi.errno
            raise OSError(err, os.strerror(err))
        self._id = None

    def pet(self) -> None:
        if self._id is None:
            raise WdogStateException('not subscribed')
        ret = _libwdog.lib.wdog_kick2(self._id, self._ack)
        if ret < 0:
            err = _libwdog.ffi.errno
            raise OSError(err, os.strerror(err))

    def extend(self, timeout: int):
        if self._id is None:
            raise WdogStateException('not subscribed')
        ret = _libwdog.lib.wdog_extend_kick(self._id, timeout, self._ack)
        if ret < 0:
            err = _libwdog.ffi.errno
            raise OSError(err, os.strerror(err))
