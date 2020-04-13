import unittest

from ultimate1541.ansi_reader import FixedAnsiReaderWriter
from ultimate1541.console_manipulator import ConsoleManipulator
from ultimate1541.pseudoscreen import PseudoScreen


def prepare_screen(data: bytes) -> PseudoScreen:
    r = FixedAnsiReaderWriter(data)
    m = ConsoleManipulator(r)
    m.refresh_screen()
    return m.screen


class TestPseudoScreen(unittest.TestCase):

    def test_parse_rectangle(self):
        s = prepare_screen(b'\x1bc\x1b[37;1m WHITE \r\n\x1b[37;2m grey')
        s.print_all()
        rect = s.parse_rectangle(0, 0)
        self.assertEqual(rect, [[(15, 'WHITE')], [(7, 'grey')]])

    def test_find_bordered_rectangle(self):
        s = prepare_screen(
            b'\x1bc\x1b(0lqqqqqqk\x1b(B\r\n'
            b'\x1b(0k\x1b(B test \x1b(0x\x1b(B\r\n'
            b'\x1b(0x\x1b(B 1111 \x1b(0x\x1b(B\r\n'
            b'\x1b(0mqqqqqqj\x1b(B\r\n')
        s.print_all()
        rect = s.find_bordered_rectangle()
        self.assertEqual(rect, (1, 1, 7, 3))

    def test_find_bordered_rectangle_nested(self):
        s = prepare_screen(
            b'\x1bc\x1b(0lqqqqqqqqqqk\x1b(B\r\n'
            b'\x1b(0x lqqqqqqk x\x1b(B\r\n'
            b'\x1b(0x x\x1b(B test \x1b(0x x\x1b(B\r\n'
            b'\x1b(0x x\x1b(B 1111 \x1b(0x x\x1b(B\r\n'
            b'\x1b(0x mqqqqqqj x\x1b(B\r\n'
            b'\x1b(0mqqqqqqqqqqj\x1b(B\r\n')
        s.print_all()
        rect = s.find_bordered_rectangle()
        self.assertEqual(rect, (3, 2, 9, 4))
