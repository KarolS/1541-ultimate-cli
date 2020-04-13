import os
import sys
import traceback
from builtins import ValueError
from typing import List, Callable, Dict

from ultimate1541 import Ultimate1541


def cmd_dir(u: Ultimate1541, params: List[str]):
    if len(params) == 0:
        return cmd_dir(u, ['/Usb0'])
    for param in params:
        if len(params) > 1:
            print('')
            print(param)
        for line in u.dir(param):
            print(line)


def cmd_upload(u: Ultimate1541, params: List[str]):
    cmd_upload_and_then(u, params, lambda: None)


def cmd_download(u: Ultimate1541, params: List[str]):
    for file in params:
        u.download_file(file, os.path.basename(file))


def cmd_run(u: Ultimate1541, params: List[str]):
    if len(params) != 1:
        raise ValueError("Exactly one parameter required")
    u.run_file(params[0])


def cmd_mount(u: Ultimate1541, params: List[str]):
    if len(params) != 1:
        raise ValueError("Exactly one parameter required")
    u.run_file(params[0])


def cmd_set_reu_size(u: Ultimate1541, params: List[str]):
    if len(params) != 1:
        raise ValueError("Exactly one parameter required")
    if params[0] in ['0', 'none', 'off', 'disabled']:
        u.set_reu_enabled(False)
    else:
        u.set_reu_enabled(True)
        u.set_reu_size(params[0])


def cmd_upload_and_run(u: Ultimate1541, params: List[str]):
    cmd_upload_one_file_and_then(u, params, lambda f: cmd_run(u, [f]))


def cmd_upload_and_mount(u: Ultimate1541, params: List[str]):
    cmd_upload_one_file_and_then(u, params, lambda f: cmd_mount(u, [f]))


def cmd_upload_one_file_and_then(u: Ultimate1541, params: List[str], callback: Callable[[str], None]):
    params = params[:]
    if len(params) > 2:
        raise ValueError("Exactly two parameters required")
    if len(params) == 1:
        params.append('/Usb0/' + os.path.basename(params[0]))
    if params[1].endswith('/'):
        params[1] += os.path.basename(params[0])
    cmd_upload_and_then(u, params, lambda: callback(params[1]))


def cmd_upload_and_then(u: Ultimate1541, params: List[str], callback: Callable[[], None]):
    if len(params) == 0:
        raise ValueError("Not enough parameters")
    if len(params) == 1:
        sources = params
        target = '/Usb0/' + os.path.basename(params[0])
    else:
        sources = params[:-1]
        target = params[-1]
        if len(params) > 2 and not target.endswith('/'):
            target += '/'
    for source in sources:
        tmp = target
        if target.endswith('/'):
            tmp += os.path.basename(source)
        u.upload_file(source, tmp, overwrite=True)  # TODO: True?
        callback()


def display_help():
    print("Usage: python u1541.py <IP address> <command>")
    print("where <command> may be:")
    print("* run <remote file> - run remote file")
    print("* mount <remote file> - mount remote file")
    print("* upload <local file> <remote file> - upload file")
    print("* ur <local file> <remote file> - upload and run file")
    print("* um <local file> <remote file> - upload and mount file")
    print("* download <remote file> - download remote file to current directory")
    print("* reu <REU size> - set REU size; use 0 to disable")
    print("* shell - start a shell")
    print("* quit - exit the shell")
    print("* help - display this list")
    return


def cmd_help(u: Ultimate1541, params: List[str]):
    display_help()


def cmd_shell(u: Ultimate1541, params: List[str]):
    print("Type quit to exit")
    while True:
        command = list(filter(lambda x:x!='', input('> ').split(' ')))
        if len(command) == 0:
            continue
        c = command[0]
        if c == 'quit' or c == 'exit':
            return
        if c == 'shell':
            continue
        if c not in COMMANDS:
            print('Invalid command ' + c)
        else:
            # noinspection PyBroadException
            try:
                COMMANDS[c](u, command[1:])
            except Exception as e:
                traceback.print_exc()


COMMANDS: Dict[str, Callable[[Ultimate1541, List[str]], None]] = {
    'dir': cmd_dir,
    'ls': cmd_dir,
    'u': cmd_upload,
    'upload': cmd_upload,
    'd': cmd_download,
    'download': cmd_download,
    'h': cmd_help,
    'help': cmd_help,
    'r': cmd_run,
    'run': cmd_run,
    'ur': cmd_upload_and_run,
    'upload_and_run': cmd_upload_and_run,
    'reu': cmd_set_reu_size,
    'shell': cmd_shell,
}


def run_command(u: Ultimate1541, command: str, params: List[str]):
    COMMANDS[command](u, params)


def do_main():
    ip_addr = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else 'help'
    params: List[str] = sys.argv[3:] if len(sys.argv) > 3 else []
    if command not in COMMANDS:
        raise ValueError('Unsupported command: ' + command)
    with Ultimate1541(ip_addr) as u:
        COMMANDS[command](u, params)
        # u.upload_file(
        #     'D:\\dokumenty\\millfork-benchmarks\\6502\\plasma-asm.prg',
        #     '/Usb0/EKSPERYMENTY/plasma-asm.prg',
        #     overwrite=True)
        # u.run_file('/Usb0/EKSPERYMENTY/plasma-asm.prg')


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        display_help()
    else:
        do_main()
