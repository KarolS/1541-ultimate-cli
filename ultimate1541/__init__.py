import os
from typing import Optional, List, Tuple, Union, Dict
from telnetlib import Telnet, WILL, DO, DONT, WONT, IAC
from ftplib import FTP, error_reply, error_perm

from ultimate1541.console_manipulator import ConsoleManipulator
from ultimate1541.ansi_reader import TelnetAnsiReaderWriter

REU_SIZES: Dict[Union[str, int, Tuple[int, str]], str] = {}

for mb in [128, 256, 512]:
    normalized = str(mb) + ' KB'
    REU_SIZES[(mb, 'k')] = normalized
    REU_SIZES[(mb, 'kB')] = normalized
    REU_SIZES[(mb, 'KB')] = normalized
    REU_SIZES[(mb, 'K')] = normalized
    REU_SIZES[mb * 1024] = normalized
    REU_SIZES[mb * 1000] = normalized
    REU_SIZES[str(mb) + 'k'] = normalized
    REU_SIZES[str(mb) + ' k'] = normalized
    REU_SIZES[str(mb) + 'kB'] = normalized
    REU_SIZES[str(mb) + ' kB'] = normalized
    REU_SIZES[str(mb) + 'K'] = normalized
    REU_SIZES[str(mb) + ' K'] = normalized
    REU_SIZES[str(mb) + 'KB'] = normalized
    REU_SIZES[str(mb) + ' KB'] = normalized

for mb in [1, 2, 4, 8, 16]:
    normalized = str(mb) + ' MB'
    REU_SIZES[(mb, 'MB')] = normalized
    REU_SIZES[(mb, 'M')] = normalized
    REU_SIZES[mb * 1024 * 1024] = normalized
    REU_SIZES[mb * 1000 * 1000] = normalized
    REU_SIZES[mb * 1024 * 1000] = normalized
    REU_SIZES[str(mb) + 'M'] = normalized
    REU_SIZES[str(mb) + ' M'] = normalized
    REU_SIZES[str(mb) + 'MB'] = normalized
    REU_SIZES[str(mb) + ' MB'] = normalized



class Ultimate1541:
    def __init__(self, ip_addr: str):
        self.ip_addr: str = ip_addr
        self.telnet: Optional[Telnet] = None
        self.ftp: Optional[FTP] = None
        self.console_manipulator: Optional[ConsoleManipulator] = None

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        self.close_ftp()
        self.close_telnet()

    def close_ftp(self):
        if self.ftp:
            self.ftp.quit()
            self.ftp = None

    def close_telnet(self):
        if self.telnet:
            self.console_manipulator.close()
            self.console_manipulator = None
            self.telnet.close()
            self.telnet = None

    def open_ftp(self):
        self.close_telnet()
        if self.ftp is None:
            self.ftp = FTP(self.ip_addr)
            # self.ftp.set_debuglevel(2)

    def open_telnet(self):
        self.close_ftp()
        if self.telnet is None:
            self.telnet = Telnet(self.ip_addr, 23, timeout=1000)
            self.telnet.set_option_negotiation_callback(option_callback)
            self.console_manipulator = ConsoleManipulator(TelnetAnsiReaderWriter(self.telnet))
            self.console_manipulator.refresh_screen()

    def get_usb_devices(self) -> List[str]:
        self.open_telnet()
        self.console_manipulator.go_home()
        menu = self.console_manipulator.get_big_menu()
        result = []
        for item in menu.items:
            if item.label.startswith('Usb'):
                result.append(item.label)
        return result

    def run_file(self, remote_path: str) -> None:
        self.do_with_file('Run', remote_path)

    def mount_file(self, remote_path: str) -> None:
        self.do_with_file('Mount disk', remote_path)

    def do_with_file(self, command: str, remote_path: str) -> None:
        path_split = split_path(remote_path)
        print(path_split)
        self.__do_with_file_internal(command, path_split[1:], device=path_split[0])

    def __do_with_file_internal(self, command: str, path: List[str], *, device: str = 'Usb0') -> None:
        if len(path) == 0:
            raise ValueError('path cannot be empty')
        self.open_telnet()
        c = self.console_manipulator
        c.go_home()
        devices = c.get_big_menu()
        for i, d in enumerate(devices.items):
            if d.label.startswith(device):
                c.select_option(i, use_return=False)
                break
        else:
            raise ValueError('Cannot find device ' + device)
        c.wait_for_device_opening(timeout=3)
        for n in path[:-1]:
            c.select_option_by_name(n, use_return=False)
        c.select_option_by_name(path[-1], use_return=True)
        c.wait_for_small_menu(timeout=1)
        c.select_option_by_name(command)

    def upload_file(self, local_path: str, remote_path: str, *, overwrite: bool = False):
        self.open_ftp()
        self.ftp.cwd(os.path.dirname(remote_path))
        if overwrite:
            self.delete_file(remote_path, quietly=True)
        with open(local_path, 'rb') as f:
            self.ftp.storbinary('STOR {}'.format(os.path.basename(remote_path)), f)

    def dir(self, remote_directory: str) -> List[str]:
        self.open_ftp()
        result = []
        self.ftp.cwd(remote_directory)
        self.ftp.dir(result.append)
        return result

    def download_file(self, remote_path: str, local_path: str):
        self.open_ftp()
        self.ftp.cwd(os.path.dirname(remote_path))
        with open(local_path, 'wb') as f:
            self.ftp.retrbinary('RETR {}'.format(os.path.basename(remote_path)), f.write)

    def delete_file(self, remote_path: str, *, quietly: bool = False):
        self.open_ftp()
        self.ftp.cwd(os.path.dirname(remote_path))
        if quietly:
            try:
                self.ftp.delete(os.path.basename(remote_path))
            except (error_perm, error_reply) as e:
                pass
        else:
            self.ftp.delete(os.path.basename(remote_path))

    def set_reu_enabled(self, enabled: bool):
        self.__set_enabled(['C64 and cartridge settings', 'RAM Expansion Unit'], enabled)

    def set_reu_size(self, size: Union[int, str, Tuple[int, str]]):
        if size not in REU_SIZES:
            raise ValueError("Invalid REU size: " + str(size))
        self.__set_setting(['C64 and cartridge settings', 'REU Size'], REU_SIZES[size])


    def set_command_interface_enabled(self, enabled: bool):
        self.__set_enabled(['C64 and cartridge settings', 'Command Interface'], enabled)

    def __set_enabled(self, option_path: List[str], enabled: bool):
        self.__set_setting(option_path, 'Enabled' if enabled else 'Disabled')

    def __set_setting(self, option_path: List[str], option_name: str):
        self.open_telnet()
        c = self.console_manipulator
        c.go_home()
        c.enter_settings()
        for option in option_path:
            c.select_option_by_name(option, use_return=True)
        c.select_option_by_name(option_name, use_return=True)
        c.leave_settings()


def option_callback(sock, cmd: bytes, opt: bytes):
    if cmd == WILL and opt == b'\x01':
        sock.sendall(IAC + DO + opt)
    elif cmd in (DO, DONT):
        sock.sendall(IAC + WONT + opt)
    elif cmd in (WILL, WONT):
        sock.sendall(IAC + DONT + opt)
    else:
        print("Unsupported IAC: " + (cmd + opt).hex())


def split_path(path: str) -> List[str]:
    result = []
    while True:
        dir, base = os.path.split(path)
        if base == '':
            result.insert(0, dir)
            break
        if dir == '':
            result.insert(0, base)
            break
        result.insert(0, base)
        path = dir
    if len(result) > 0 and result[0] == '/':
        return result[1:]
    return result

