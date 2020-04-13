from typing import Tuple, Optional, List
from time import sleep

from ultimate1541.menu import Menu
from ultimate1541.pseudoscreen import PseudoScreen
from ultimate1541.ansi_reader import AnsiReaderWriter

ANSI_UP = b'\x1b[A'
ANSI_DOWN = b'\x1b[B'
ANSI_RIGHT = b'\x1b[C'
ANSI_LEFT = b'\x1b[D'
ANSI_RETURN = b'\r'
ANSI_F2 = b'\x1b[12~'


class ConsoleManipulator:
    def __init__(self, reader: AnsiReaderWriter):
        self.screen: PseudoScreen = PseudoScreen()
        self.reader: AnsiReaderWriter = reader

    def open(self):
        pass

    def close(self):
        self.reader.write(b'\x1b\x1b' * 10)

    def refresh_screen(self):
        sleep(0.2)
        while True:
            t = self.reader.read_token()
            if t is None:
                return
            self.screen.write(t)

    def __rect_to_menu(self, rect: [[Tuple[int, str]]]) -> Menu:
        menu = Menu()
        for ix, line in enumerate(rect):
            if len(line) == 0:
                break
            if len(line) == 4 and line[3][1] == '-':
                break
            t1 = line[0][1]
            if t1 != '' and not t1.isspace():
                selected = False
                for token in line:
                    if token[0] == 15:
                        selected = True
                t2 = line[1][1] if len(line) > 1 else ''
                menu.add_item(t1, t2, selected)
        return menu

    def get_big_menu(self) -> Menu:
        rect: [[Tuple[int, str]]] = self.screen.parse_rectangle(0, 2, None, 24)
        return self.__rect_to_menu(rect)

    def get_small_menu(self) -> Optional[Menu]:
        maybe = self.screen.find_bordered_rectangle()
        if maybe is None:
            return None
        rect: [[Tuple[int, str]]] = self.screen.parse_rectangle(*maybe)
        return self.__rect_to_menu(rect)

    def wait_for_small_menu(self, timeout: float) -> None:
        while timeout >= 0:
            self.refresh_screen()
            if self.get_small_menu() is not None:
                return
            timeout -= 0.2
        raise TimeoutError('Small menu timed out')

    def wait_for_device_opening(self, timeout: float) -> None:
        while timeout >= 0:
            self.refresh_screen()
            if self.screen.char_at(0, 24) == '/':
                return
            if self.screen.char_at(0, 23) == '/':
                return
            timeout -= 0.2
        self.screen.print_all()
        raise TimeoutError('Device opening timed out')

    def select_option(self, index: int, *, use_return: Optional[bool] = None) -> None:
        self.refresh_screen()
        menu = self.get_small_menu()
        if use_return is None:
            if menu is None:
                enter = ANSI_RIGHT
            else:
                enter = ANSI_RETURN
        elif use_return:
            enter = ANSI_RETURN
        else:
            enter = ANSI_RIGHT
        if menu is None:
            menu = self.get_big_menu()
        if menu is not None and len(menu.selected) == 1:
            return self.select_option_relative(index - menu.selected[0], use_return=(enter == ANSI_RETURN))
        for j in range(40):
            self.reader.write(ANSI_UP)
        for j in range(index):
            self.reader.write(ANSI_DOWN)
        self.reader.write(enter)
        self.refresh_screen()

    def select_option_relative(self, offset: int, *, use_return: bool = False) -> None:
        if use_return:
            enter = ANSI_RETURN
        else:
            enter = ANSI_RIGHT
        if offset < 0:
            for j in range(-offset):
                self.reader.write(ANSI_UP)
        else:
            for j in range(offset):
                self.reader.write(ANSI_DOWN)
        self.reader.write(enter)
        self.refresh_screen()

    def select_option_by_name(self, name: str, *, use_return:Optional[bool] = None) -> None:
        self.refresh_screen()
        small_menu = self.get_small_menu()
        big_menu = None
        index: Optional[int] = None
        if small_menu is None:
            enter = ANSI_RIGHT
            big_menu = self.get_big_menu()
            index = big_menu.lookup_by_label(name)
        else:
            enter = ANSI_RETURN
            index = small_menu.lookup_by_label(name)
        if use_return is not None:
            enter = ANSI_RETURN if use_return else ANSI_RIGHT
        if index is None:
            # print('small menu: ' + str(small_menu))
            # print('big menu: ' + str(big_menu))
            menu = small_menu if small_menu is not None else big_menu
            raise ValueError('Item labelled ' + name + ' does not exist! Available items: ' + ', '.join(map(lambda i:i.label, menu.items)))
        for j in range(index):
            self.reader.write(ANSI_DOWN)
        self.reader.write(enter)
        sleep(0.2)
        self.refresh_screen()

    def go_back(self):
        self.reader.write(ANSI_LEFT)
        self.refresh_screen()

    def go_home(self):
        for j in range(8):
            self.reader.write(ANSI_LEFT)
        self.refresh_screen()

    def enter_settings(self):
        self.reader.write(ANSI_F2)
        self.wait_for_small_menu(timeout=1)
        self.refresh_screen()

    def leave_settings(self):
        self.reader.write(b'\x1b ')
        while self.get_small_menu() is not None:
            self.refresh_screen()





        


