import os
from time import sleep
from time import ctime

#from proc import Proc
#from proc import getpids
from core.proc import Proc, getpids

DEFAULT_INTERVAL = 1

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
            except (OSError, IOError):
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

nadbg = NADBG()
