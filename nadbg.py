from core.welprompt import CLUI
from core.nadbg import *

# these codes for debug
from IPython import embed
import traceback as tb
import sys
def excepthook(type, value, traceback):
    tb.print_last()
    embed()
sys.excepthook = excepthook

# load plugins
try:
    from plugins.hi_loader import hi # heapinspect
except ImportError:
    print('Use `git submodule init` to download plugins')
    exit()



if __name__ == '__main__':
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

    # plugins
    def hi_plugin(command='help', *args):
        ''' Heapinspect plugin '''
        func = getattr(hi, command)
        return func(*args)
    
    ui.commands['hi'] = hi_plugin

    ui.run()