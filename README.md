# nadbg

nadbg is designed to analyze memory of the Linux process.

__core feature__
- ptrace free
- extensible
- easy to use
- blabla......

__future feature__
- heap analyze
- ASLR/PIE support
- blabla......

# usage

Start this appilication.

```py
python nadbg.py
```

Use `help` or `?` to get some help.

## attach

nadbg support `path`, `binary name`, `pid`.

```
[nadbg]  > attach /bin/cat
/bin/cat not found
attach /bin/cat failed
```

well, this is a mistake.

```
[nadbg] /bin/cat > attach /usr/bin/cat
attach /usr/bin/cat success. pid: 10696
[nadbg] /usr/bin/cat >
```

```
[nadbg]  > attach cat
attach cat success. pid: 10696
[nadbg] cat >
```

```
[nadbg]  > attach 10696
attach 10696 success. pid: 10696
[nadbg] 10696 >
```

## memory dump

memory dump is similar to those of `pwndbg`.

```
[nadbg] /usr/bin/cat > dq 0x7fffffffe270 4
0x7fffffffe270: 0000000000000001 00007fffffffe588
0x7fffffffe280: 0000000000000000 00007fffffffe595
[nadbg] /usr/bin/cat > dd 0x7fffffffe270 4
0x7fffffffe270: 00000001 00000000 ffffe588 00007fff
[nadbg] /usr/bin/cat > db 0x7fffffffe270 16
0x7fffffffe270: 01 00 00 00 00 00 00 00 88 e5 ff ff ff 7f 00 00
[nadbg] /usr/bin/cat > ds 0x7fffffffe588 13
'/usr/bin/cat\x00'
```

## memory search

memory search is similar to that of `peda`.

```
[nadbg] /usr/bin/cat > find /bin/cat
[0] 0x7fffffffe58c
[1] 0x7fffffffefcd
[2] 0x7fffffffefef
[nadbg] /usr/bin/cat > find 0x7fffffffe588
[0] 0x55555555f278
[1] 0x7fffffffe278
```

## memory watch

`memory watcher` is designed to scan/print memory.

well, it's designed to free you from `dq`, `dq` and `dq`. :)

```
[nadbg] /usr/bin/cat > wq 0x7fffffffe278 1
[nadbg] /usr/bin/cat > ws 0x7fffffffe588 13
[nadbg] /usr/bin/cat > p
[0] 1 qword
0x7fffffffe278: 00007fffffffe588
[1] 13 str
0x7fffffffe588: '/usr/bin/cat\x00'
[nadbg] /usr/bin/cat >
```

also, there's a loop printer for you. by default, it has a scan interval of 1 sec. it will only print message when the watched memory changed.

```
[nadbg] /usr/bin/cat > print_forever
[0] 1 qword
0x7fffffffe278: 00007fffffffe588
[1] 13 str
0x7fffffffe588: '/usr/bin/cat\x00'

[0] 1 qword
0x7fffffffe278: 00007fffffffe588
[1] 13 str
0x7fffffffe588: '\xef\xbe\xad\xde/bin/cat\x00'

[0] 1 qword
0x7fffffffe278: 00007fffdeadbeef
[1] 13 str
0x7fffffffe588: '\xef\xbe\xad\xde/bin/cat\x00'

^C
KeyboardInterrupt
```

just use `ctrl + c` to stop it.

## other?

tell me what you want. then i make one for you.