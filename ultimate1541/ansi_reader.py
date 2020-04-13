from typing import Optional, Union
from telnetlib import Telnet
from ultimate1541.escape_sequence import EscapeSequence
from abc import ABC, abstractmethod

V100_ACS = {
    'j': '┘',
    'k': '┐',
    'l': '┌',
    'm': '└',
    'n': '┼',
    'q': '─',
    't': '├',
    'u': '┤',
    'v': '┴',
    'w': '┬',
    'x': '│',
}


class AnsiReaderWriter(ABC):
    def __init__(self):
        self.shifted: bool = False

    @abstractmethod
    def read_byte(self) -> Optional[int]:
        pass

    @abstractmethod
    def write(self, data: bytes) -> None:
        pass

    def read_token(self) -> Union[None, str, EscapeSequence]:
        c = self.read_byte()
        if c is None:
            return None
        if type(c) != int:
            raise TypeError("c should be int, is " + str(type(c)))
        if c != 0x1b:
            # TODO: shifted character set
            char = chr(c)
            if self.shifted and char in V100_ACS:
                return V100_ACS[char]
            return char
        cmd1 = chr(self.read_byte())
        if cmd1 == '[':
            params = [0]
            while True:
                c = self.read_byte()
                if c == ord(';') or c == ord(','):
                    params.append(0)
                elif 0x30 <= c <= 0x39:
                    params[-1] *= 10
                    params[-1] += c - 0x30
                else:
                    return EscapeSequence(command=cmd1 + chr(c), params=params)
        elif cmd1 == '(':
            cmd2 = chr(self.read_byte())
            if cmd2 == 'B':
                self.shifted = False
            elif cmd2 == '0':
                self.shifted = True
            else:
                raise ValueError('Unsupported escape sequence: ESC ' + cmd1 + cmd2)
            return self.read_token()
        elif cmd1 == 'c':
            return EscapeSequence('c', [])
        else:
            raise ValueError('Unsupported escape sequence: ESC ' + cmd1)


class TelnetAnsiReaderWriter(AnsiReaderWriter):

    def __init__(self, tn: Telnet):
        super().__init__()
        self.tn: Telnet = tn
        self.buf: bytes = b''
        self.cursor: int = 0

    def write(self, data: bytes):
        self.tn.write(data)

    def read_byte(self) -> Optional[int]:
        if self.cursor >= len(self.buf):
            self.buf = self.tn.read_eager()
            self.cursor = 0
        if self.buf == b'':
            return None
        c = self.buf[self.cursor]
        self.cursor += 1
        return c


class FixedAnsiReaderWriter(AnsiReaderWriter):

    def __init__(self, buf: bytes):
        super().__init__()
        if type(buf) != bytes:
            raise TypeError("buf should be bytes")
        self.buf: bytes = buf
        self.cursor: int = 0

    def write(self, data: bytes):
        pass

    def read_byte(self) -> Optional[int]:
        if self.cursor >= len(self.buf):
            return None
        c = self.buf[self.cursor]
        self.cursor += 1
        return c
