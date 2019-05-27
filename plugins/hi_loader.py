import os
import sys
FILE_PATH = os.path.expanduser(__file__)
FILE_PATH = os.path.abspath(FILE_PATH)
if os.path.islink(FILE_PATH):
    FILE_PATH = os.readlink(FILE_PATH)
DIR_PATH = os.path.dirname(FILE_PATH)
HEAP_INSPECT_PATH = os.path.join(DIR_PATH, './heapinspect')
sys.path.insert(0, HEAP_INSPECT_PATH)
from heapinspect.core import *
from common import common

def to_int(val):
    """
    Convert a string to int number
    from https://github.com/longld/peda
    """
    try:
        return int(str(val), 0)
    except:
        return None


def normalize_argv(args, size=0):
    """
    Normalize argv to list with predefined length
    from https://github.com/longld/peda
    """
    args = list(args)
    for (idx, val) in enumerate(args):
        if to_int(val) is not None:
            args[idx] = to_int(val)
        if size and idx == size:
            return args[:idx]

    if size == 0:
        return args
    for i in range(len(args), size):
        args += [None]
    return args


class HeapInspectCmd(object):
    def __init__(self):
        self.commands = [cmd for cmd in dir(self) if callable(getattr(self, cmd))]

    @property
    def pid(self):
        return common.pid

    def heap(self, *args):
        args = normalize_argv(args)
        hi = HeapInspector(self.pid)
        if 'raw' in args:
            hs = HeapShower(hi)
            if 'rela' in args:
                hs.relative = True
            if 'all' in args:
                print(hs.heap_chunks)
            print(hs.fastbins)
            print(hs.unsortedbins)
            print(hs.smallbins)
            print(hs.largebins)
            print(hs.tcache_chunks)            
        else:
            pp = PrettyPrinter(hi)
            print(pp.all)

    def heapchunks(self, *args):
        args = normalize_argv(args)
        hi = HeapInspector(self.pid)
        if 'rela' in args:
            hs.relative = True
        print(hs.heap_chunks)

    def tcache(self, *args):
        args = normalize_argv(args)
        hi = HeapInspector(self.pid)
        if 'raw' in args:
            hs = HeapShower(hi)
            if 'rela' in args:
                hs.relative = True
            print(hs.tcache_chunks)            
        else:
            pp = PrettyPrinter(hi)
            print(pp.tcache_chunks)

    def fastbins(self, *args):
        args = normalize_argv(args)
        hi = HeapInspector(self.pid)
        if 'raw' in args:
            hs = HeapShower(hi)
            if 'rela' in args:
                hs.relative = True
            print(hs.fastbins)            
        else:
            pp = PrettyPrinter(hi)
            print(pp.fastbins)

    def smallbins(self, *args):
        args = normalize_argv(args)
        hi = HeapInspector(self.pid)
        if 'raw' in args:
            hs = HeapShower(hi)
            if 'rela' in args:
                hs.relative = True
            print(hs.smallbins)            
        else:
            pp = PrettyPrinter(hi)
            print(pp.smallbins)

    def largebins(self, *args):
        args = normalize_argv(args)
        hi = HeapInspector(self.pid)
        if 'raw' in args:
            hs = HeapShower(hi)
            if 'rela' in args:
                hs.relative = True
            print(hs.largebins)            
        else:
            pp = PrettyPrinter(hi)
            print(pp.largebins)

    def unsortedbins(self, *args):
        args = normalize_argv(args)
        hi = HeapInspector(self.pid)
        if 'raw' in args:
            hs = HeapShower(hi)
            if 'rela' in args:
                hs.relative = True
            print(hs.unsortedbins)            
        else:
            pp = PrettyPrinter(hi)
            print(pp.unsortedbins)

    def help(self):
        help_string = '''HeapInspect for gdb
https://github.com/matrix1001/heapinspect

Prefix:
hi

Commands:
help ---- show this help text.
heap ---- show all info about heap.
heapchunks, tcache, fastbins, smallbins, largebins, unsortedbins ---- show specific chunks.

Acceptable args:
all ---- for `heap` only. show heapchunks.
raw ---- show more detailed chunk info.
rela ---- with `raw` only. show relative address.

Examples:
`hi help`
`hi heap`
`hi heap all raw rela`
`hi fastbins raw`
`hi smallbins`
`hi tcache`
'''
        print(help_string)

hi = HeapInspectCmd()
