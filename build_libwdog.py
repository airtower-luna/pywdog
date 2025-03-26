import cffi
import sys

ffibuilder = cffi.FFI()
ffibuilder.cdef('''
int wdog_ping(void);
int wdog_subscribe(char *label, unsigned int timeout, unsigned int *next_ack);
int wdog_unsubscribe(int id, unsigned int ack);
int wdog_extend_kick(int id, unsigned int timeout, unsigned int *ack);
int wdog_kick2(int id, unsigned int *ack);
int wdog_enable(int enable);
int wdog_status(int *status);
''')
ffibuilder.set_source('_libwdog', r'''
#include <wdog/wdog.h>
''', libraries=['wdog'])

if __name__ == '__main__':
    ffibuilder.emit_c_code(sys.argv[1])
