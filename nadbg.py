import os
from time import sleep
from time import ctime

from welprompt import CLUI
from proc import Proc
from proc import getpids

DEFAULT_INTERVAL = 1


# these codes for debug
from IPython import embed
import traceback as tb
import sys
def excepthook(type, value, traceback):
    tb.print_last()
    embed()
sys.excepthook = excepthook



def get_int(_min, _max, prompt=''):
    while True:
        s = input(prompt)
        i = int(s)
        if i >= _min and i <= _max:
            return i



class MemWatches(object):
    def __init__(self):
        self.list = []
    def __getitem__(self, i):
        return self.list[i]
    @property
    def count(self):
        return len(self.list)
    def add(self, addr, typ, size):
        watch = (addr, typ, size)
        self.list.append(watch)
    def remove(self, addr_or_idx):
        if addr_or_idx < 0 or self.count == 0:
            raise ValueError('Invalid watch index {} to remove'.format(addr_or_idx))
        elif addr_or_idx < self.count:
            self.list.pop(addr_or_idx)
            return
        else:
            for watch in self.list:
                addr, typ, size = watch
                if addr == addr_or_idx:
                    self.list.remove(watch)
                    return
            raise ValueError('Invalid watch addr {:#x} to remove'.format(addr_or_idx))

    
def memfmt(mem, addr, type_size, perline=16):
    total_size = len(mem)
    count = int(total_size / type_size) + int(total_size % type_size != 0)

    fmt = '{:#x}: {}'
    hex_lst = []
    for i in range(count):
        start = type_size * i
        end = type_size * (i+1)
        mem_block = mem[start:end][::-1] # little endian
        hex_lst.append(mem_block.encode('hex'))

    lines = []
    nline = int(total_size / perline) + int(total_size % perline != 0)
    nhex = perline / type_size
    for i in range(nline):
        start_addr = addr + i * perline
        start = i * nhex
        end = (i+1) * nhex
        if end > len(hex_lst):
            end = len(hex_lst)
        mem_str = ' '.join(hex_lst[start:end])
        lines.append(fmt.format(start_addr, mem_str))
    return '\n'.join(lines)


class NADBG(object):
    def __init__(self):
        self.pid = 0
        self.s = ''
        self.watches = MemWatches()

    def _type_to_memsize(self, typ):
        type_to_memsize = {
            'byte': 1,
            'str': 1,
            'int': 4,
            'word': 2,
            'dword': 4,
            'qword': 8,
        }
        if self.proc.arch == '32':
            type_to_memsize['size_t'] = 4
        elif self.proc.arch == '64':
            type_to_memsize['size_t'] = 8
        type_to_memsize['ptr'] = type_to_memsize['size_t']
        return type_to_memsize[typ]

    @property
    def proc(self):
        if self.pid == 0:
            return None
        else:
            return Proc(self.pid)

    @property
    def watches_info(self):
        contents = []
        for idx, watch in enumerate(self.watches):
            addr, typ, size = watch
            typ_size = self._type_to_memsize(typ)
            total = size * typ_size
            mem = self.proc.read(addr, total)
            if typ == 'str':
                content = '[{}] {} {}\n'.format(idx, size, typ) 
                content += '{:#x}: {}'.format(addr, repr(mem))
            else:
                content = '[{}] {} {}\n'.format(idx, size, typ) + memfmt(mem, addr, typ_size)
            contents.append(content)
        return '\n'.join(contents)


    def memdump(self, addr, typ, size):
        typ_size = self._type_to_memsize(typ)
        total = size * typ_size
        mem = self.proc.read(addr, total)
        if typ == 'str':
            content = repr(mem)
        else:
            content = memfmt(mem, addr, typ_size)
        return content

    def attach(self, s):
        self.s = s
        def is_candidate(s, pid):
            try:
                p = Proc(pid)
                if os.path.exists(s):
                    # s is path
                    path = os.path.abspath(s)
                    return path == p.path
                else:
                    # s is filename
                    return s == p.name
            except OSError:
                return False

        if s.isdigit():
            self.set_pid(int(s))
        else:
            candidates = []
            # assume s is str
            for pid in getpids():
                if is_candidate(s, pid):
                    candidates.append(pid)
            sz = len(candidates)
            if sz == 0:
                print('{} not found'.format(s))
                self.set_pid(0)
            elif sz == 1:
                self.set_pid(candidates[0])
            else:
                # multiple candidates
                for pid in candidates:
                    p = Proc(pid)
                    print('{}: {} {}'.format(pid, p.username, p.path))
                choise = get_int(0, sz-1, 'choose from 0 to {}: '.format(sz-1))
                self.set_pid(candidates[choise])
        return self.pid

    def set_pid(self, pid):
        self.pid = pid
        if pid:
            self.do_check()
            self.s = self.proc.path

    def do_check(self):
        if not os.access('/proc/{}/mem'.format(self.pid), os.R_OK):
            print('process {} died or not readable'.format(self.pid))
            if self.s:
                print('trying to reattach to {}'.format(self.s))
                pid = self.attach(self.s)
                if pid:
                    print('reattaching success. pid: {}'.format(pid))
                else:
                    raise RuntimeError('reattaching failed.')
            else:
                self.pid = 0


if __name__ == '__main__':
    nadbg = NADBG()
    interval = DEFAULT_INTERVAL
    def set_value(key, val):
        '''set global values.
        args:
            key: key
            val: val
        '''
        key_to_obj = {
            'interval': (interval, int),
        }
        if key in key_to_obj:
            obj, typ = key_to_obj[key]
            obj = typ(val)
        else:
            print('invalid key')


    def attach(s):
        '''attach to a process. name and pid are supported
        args:
            s: a binary name or its pid, also support path
        '''
        pid = nadbg.attach(s)
        if pid == 0:
            print('attach {} failed'.format(s))
        else:
            print('attach {} success. pid: {}'.format(s, pid))

    def watch(typ, addr, size='1'):
        '''set memory watch point for the attached process.
        args:
            typ: supported type -- byte str int dword qword ptr size_t
            addr: the address you want to set watch point. (e.g. 0x602010  0x7fff8b4000)
            size: total_size = sizeof(typ) * size
        '''
        if addr.startswith('0x'):
            addr = int(addr[2:], 16)
        else:
            addr = int(addr)
        if size.startswith('0x'):
            size = int(size[2:], 16)
        else:
            size = int(size)
        nadbg.watches.add(addr, typ, size)


    def watcher_print():
        '''print out all watch point information. no args needed.
        '''
        nadbg.do_check()
        print(nadbg.watches_info)

    def print_forever():
        '''print out all watch point information when there is a change.
        use `set interval 0.5` to let it check each 0.5 sec. default is 1.
        '''
        pre_msg = ''
        while True:
            nadbg.do_check()
            msg = nadbg.watches_info
            if msg != pre_msg:
                pre_msg = msg
                print(msg)
                print('')
            sleep(interval)

    def dump(typ, addr, size='1'):
        '''dump memory for the attached process.
        args:
            typ: supported type -- byte str int dword qword ptr size_t
            addr: the address you want to set watch point. (e.g. 0x602010  0x7fff8b4000)
            size: total_size = sizeof(typ) * size
        '''
        if addr.startswith('0x'):
            addr = int(addr[2:], 16)
        else:
            addr = int(addr)
        if size.startswith('0x'):
            size = int(size[2:], 16)
        else:
            size = int(size)
        nadbg.do_check()
        print(nadbg.memdump(addr, typ, size))

    def psinfo(key=None):
        '''get process info.
        args:
            key: the name of the info.
        '''
        nadbg.do_check()
        if key == 'vmmap':
            print('\n'.join([str(map) for map in nadbg.proc.vmmap]))
        elif key == 'bases':
            print('\n'.join(['{}: {:#x}'.format(base[0], base[1]) for base in nadbg.proc.bases.items()]))
        elif key == 'canary':
            print(hex(nadbg.proc.canary))
        else:
            info = []
            info.append('process path: {}'.format(nadbg.proc.path))
            info.append('arch: {}'.format(nadbg.proc.arch))
            info.append('libc: {}'.format(nadbg.proc.libc))
            info.append('prog address: {:#x}'.format(nadbg.proc.bases['prog']))
            info.append('libc address: {:#x}'.format(nadbg.proc.bases['libc']))
            print('\n'.join(info)) 

    def find(s):
        '''Search in all memory of the attached process.

        args:
            s: The content to search. use `0x` to search int.
        '''
        nadbg.do_check()
        results = nadbg.proc.search_in_all(s)
        if not results:
            print('not found')
        else:
            contents = []
            for idx, ele in enumerate(results):
                addr, memhex = ele
                content = '[{}] {:#x}'.format(idx, addr)
                contents.append(content)
            print('\n'.join([_ for _ in contents]))
            

    def prompt_status():
        return nadbg.s



    ui = CLUI('nadbg')
    ui.commands['set'] = set_value
    ui.commands['attach'] = attach
    ui.commands['watch'] = watch
    ui.commands['print'] = watcher_print
    ui.commands['print_forever'] = print_forever
    ui.commands['dump'] = dump
    ui.commands['info'] = psinfo
    ui.commands['find'] = find
    ui.prompt_status = prompt_status

    ui.alias['wb'] = 'watch byte'
    ui.alias['ws'] = 'watch str'
    ui.alias['ww'] = 'watch word'
    ui.alias['wd'] = 'watch dword'
    ui.alias['wq'] = 'watch qword'

    ui.alias['db'] = 'dump byte'
    ui.alias['ds'] = 'dump str'
    ui.alias['ww'] = 'dump word'
    ui.alias['dd'] = 'dump dword'
    ui.alias['dq'] = 'dump qword'

    ui.alias['vmmap'] = 'info vmmap'
    ui.alias['canary'] = 'info canary'

    ui.alias['at'] = 'attach'
    ui.alias['p'] = 'print'
    ui.alias['q'] = 'exit'

    ui.run()