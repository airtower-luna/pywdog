# pywdog

This package is a wrapper for libwdog provided by
[watchdogd](https://github.com/troglobit/watchdogd). It lets Python
services subscribe to the watchdogd supervisor (if enabled in
watchdogd configuration). If a subscribed service fails to report
regularly, watchdogd will either reset the system, or run its
supervisor script, depending on its configuration.

## Usage

Using pywdog in your application generally requires three things:

1. During startup, create a `Wdog` object with a label of your choice,
   and *subscribe* to the watchdogd supervisor. The subscribe call
   sets the timeout for the subscription in seconds. Note that
   watchdogd defines a minimum timeout (1s as of version 4.0), setting
   a value that is too will raise a `ValueError`.
2. While your application is running, ensure that the watchdog gets
   *pet* regularly, with two pets less than the timeout apart.
3. If your application gets shut down intentionally (that is,
   watchdogd should *not* reset the system when it fails to report
   in), *unsubscribe* from the supervisor.

Example:

```python
import wdog

w = wdog.Wdog('example')
w.subscribe(2.0)
for _ in range(5):
    time.sleep(.5)
    w.pet()
w.unsubscribe()
```

You can change the timeout of an active subscription with
`Wdog.set_timeout()`.
