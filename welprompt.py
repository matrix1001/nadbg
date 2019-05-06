# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys
if sys.version_info.major < 3:
    input = raw_input

import os
import subprocess
import time 
import six
from time import sleep
import traceback as tb

 
class CLUI(object):
    def __init__(self, name=''):
        self.name = name
        self.commands = {
            'help':self.help,
            'exit':self.exit,
        }
        self.prompt_status = None
        self.alias = {'?':'help'}
    
    def setup_readline(self):
        try:
            import readline
            import atexit
            history_file = "./.{}_history".format(self.name)
            if not os.path.exists(history_file):
                open(history_file, 'a+').close()

            readline.read_history_file(history_file)
            # readline.set_history_length(history_length)
            atexit.register(readline.write_history_file, history_file)

            readline.parse_and_bind('set enable-keypad on')

            readline.set_completer(self.complete)
            readline.set_completer_delims(' \t\n;')
            readline.parse_and_bind("tab: complete")
        except:
            pass
    
    def complete(self, text, state):
        candidates = [x for x in self.commands.keys() + self.alias.keys() if x.startswith(text)]
        return candidates[state] + ' '

    def get_prompt(self):
        pre = '[{}] '.format(self.name)
        if self.prompt_status:
            return pre + '{} > '.format(self.prompt_status())
        else:
            return pre + '> '

    def run(self):
        self.setup_readline()
        while True:
            try:
                prompt = self.get_prompt()
                line = input(prompt)
                msg = self._handler(line)
                if msg:
                    print(msg)
                
            except KeyboardInterrupt:
                print('\nKeyboardInterrupt')
                continue
            except EOFError:
                break

            #except Exception as e:
            #    print(e)

    def _handler(self, line):
        if line == '':
            return
        elif line[0] == '!': # shell
            return self._execve(line[1:])
            
        elif line[0] == '%': # python
            try:
                six.exec_(line[1:], locals(), globals())
            except Exception as e:
                return str(e)
        else:
            command_name, args = line.split()[0], line.split()[1:]
            if command_name in self.commands.keys():
                command_func = self.commands[command_name]
                try:
                    return command_func(*args)
                except (TypeError, ValueError) as e:
                    # argument error
                    return str(e) + '\n' + self.help(command_name)
                except RuntimeError as e:
                    # just need to stop
                    return str(e)
                except Exception as e:
                    # other exception
                    return tb.format_exc()
            elif command_name in self.alias:
                new_line = line.replace(command_name, self.alias[command_name], 1) + ' '
                return self._handler(new_line)
            else:
                return 'no such command "{}"\n\n'.format(command_name) + self.help()

    def _execve(self, cmd):
        return os.popen(cmd).read()

    def exit(self):
        exit()

    def help(self, *args):
        "print help message"
        msg = ''
        if args == (): 
            msg = '?: alias of help\n!: execve shell command\n%: exec python script\nctrl+d: exit\nctrl+c: stop command\n'
            for alia in sorted(self.alias.keys()):
                msg += '{} (alias): {}\n'.format(alia, self.alias[alia])
            args = sorted(self.commands.keys())
        for command in args:
            if command in self.commands.keys():
                doc = self.commands[command].__doc__
                if doc:
                    if '\n' not in doc:
                        msg += '{}: {}\n'.format(command, doc)
                    else:
                        indent = '\n    '
                        lines = doc.splitlines()
                        old_indent = lines[1].replace(lines[1].strip(), '')
                        stripped = indent.join([line.replace(old_indent, '', 1) for line in lines])
                        msg += '{}: {}\n'.format(command, stripped)
                else:
                    msg += '{}: {}\n'.format(command, "not documented")
            else:
                msg += '{}: {}\n'.format(command, 'unkown command')
        return msg

if __name__ == '__main__':
    c = CLUI('testapp')

    def printf(fmt, *args):
        print(fmt % args)

    def mycommand(cmd):
        '''this is just a case
        for stupid test'''
        print(cmd)
        
    def prompt_status():
        return os.getcwd()
    
    def error_test():
        return 1/0
    
    def error_test2():
        raise ValueError('test value error')
        
    c.prompt_status = prompt_status
    c.commands['printf'] = printf
    c.commands['mycommand'] = mycommand
    c.commands['error'] = error_test
    c.commands['e2'] = error_test2
    c.run()