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

class MemWatcher(object):
    def __init__(self):
        self.proc = None
        self.watches = [] # element: (addr, typ, size)
        self.mem_perline = 16

    def _type_to_memsize(self, typ):
        type_to_memsize = {
            'byte': 1,
            'str': 1,
            'int': 4,
            'dword': 4,
            'qword': 8,
        }
        if self.proc.arch == '32':
            type_to_memsize['size_t'] = 4
        elif self.proc.arch == '64':
            type_to_memsize['size_t'] = 8
        type_to_memsize['ptr'] = type_to_memsize['size_t']
        return type_to_memsize[typ]

    def _get_global_info(self):
        return 'number of watches: {}'.format(len(self.watches))

    def get_msg(self):
        def _parse_watch(watch):
            def _mem_chk(addr, size):
                return True
            addr, typ, size = watch
            typ_size = self._type_to_memsize(typ)
            total_size = typ_size * size
            banner = '{:#x} {} {}\n'.format(addr, typ, size)
            if _mem_chk(addr, total_size):
                fmt = '{:#x}: {}'
                mem = self.proc.read(addr, total_size)
                if typ == 'str':
                    return banner + fmt.format(addr, repr(mem))
                else:
                    hex_lst = []
                    for i in range(size):
                        start = typ_size*i
                        end = typ_size*(i+1)
                        mem_block = mem[start:end][::-1] # little endian
                        hex_lst.append(mem_block.encode('hex'))

                    msg_lst = []
                    nline = total_size / self.mem_perline + bool(total_size % self.mem_perline)
                    nhex = self.mem_perline / typ_size
                    for i in range(nline):
                        start_addr = addr + i * self.mem_perline
                        start = i * nhex
                        end = (i+1) * nhex
                        if end > len(hex_lst):
                            end = len(hex_lst)
                        mem_str = ' '.join(hex_lst[start:end])
                        msg_lst.append(fmt.format(start_addr, mem_str))

                    return banner + '\n'.join(msg_lst)

            else:
                print("illegle mem area: {}-{}".format(addr, addr + total_size))
                return ''

        msg_lst = []
        msg_lst.append(self._get_global_info())
        for watch in self.watches:
            msg_lst.append(_parse_watch(watch))
        return '\n'.join(msg_lst)

    def add_watch(self, watch):
        def _chk_watch(watch):
            return True

        if _chk_watch(watch):
            self.watches.append(watch)
        else:
            print('invalid watch')

    def remove_watch(self, wid):
        def _chk_wid(wid):
            if wid < 0 or wid >= len(self.watches):
                return False
            else:
                return True

        if _chk_wid(wid):
            self.watches.__delitem__(wid)
        else:
            print('invalid watch id')

    def set_pid(self, pid):
        def _chk_pid(pid):
            return True

        if _chk_pid(pid):
            self.proc = Proc(pid)
        else:
            print('invalid pid')


class NADBG(object):
    def __init__(self):
        self.pid = 0
        self.s = ''
        self.mem_watcher = MemWatcher()

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
        self.do_check()
        self.mem_watcher.set_pid(pid)

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

    def watch(typ, addr, size):
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
        nadbg.mem_watcher.add_watch((addr, typ, size))


    def watcher_print():
        '''print out all watch point information. no args needed.
        '''
        nadbg.do_check()
        print(nadbg.mem_watcher.get_msg())

    def print_forever():
        '''print out all watch point information when there is a change.
        use `set interval 0.5` to let it check each 0.5 sec. default is 1.
        '''
        pre_msg = ''
        while True:
            nadbg.do_check()
            msg = nadbg.mem_watcher.get_msg()
            if msg != pre_msg:
                pre_msg = msg
                print(msg)
                print('')
            sleep(interval)
    
    def prompt_status():
        return nadbg.s



    ui = CLUI('nadbg')
    ui.commands['set'] = set_value
    ui.commands['attach'] = attach
    ui.commands['watch'] = watch
    ui.commands['print'] = watcher_print
    ui.commands['print_forever'] = print_forever
    ui.prompt_status = prompt_status

    ui.alias['wb'] = 'watch byte'
    ui.alias['ws'] = 'watch str'
    ui.alias['wd'] = 'watch dword'
    ui.alias['wq'] = 'watch qword'

    ui.alias['at'] = 'attach'
    ui.alias['p'] = 'print'
    ui.alias['q'] = 'exit'

    ui.run()