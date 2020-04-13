from typing import Optional, Union, Tuple, List

from ultimate1541.escape_sequence import EscapeSequence

COLOUR_NAMES = [
    'Blk',
    'Red',
    'Grn',
    'Yel',
    'Blu',
    'Mag',
    'Cya',
    'Gr1',
    'Gr2',
    'BrR',
    'BrG',
    'BrY',
    'BrB',
    'BrM',
    'BrC',
    'Wht',
]


class PseudoScreen:
    def __init__(self):
        self.text: List[str] = []
        self.colours: List[List[int]] = []
        self.cursor_x = 0
        self.cursor_y = 0
        self.text_colour = 7

    def line_count(self):
        return len(self.text)

    def write(self, t: Union[None, str, EscapeSequence]):
        # print(t)
        if t is None:
            return
        elif t == '\r':
            self.cursor_x = 0
        elif t == '\n':
            self.cursor_y += 1
        elif type(t) is str:
            if len(t) != 1:
                raise ValueError('Cannot print ' + t)
            while len(self.text) <= self.cursor_y:
                self.text.append('')
            while len(self.colours) <= self.cursor_y:
                self.colours.append([])
            cols: [int] = self.colours[self.cursor_y]
            chrs: str = self.text[self.cursor_y]

            def find_last_colour_before(y):
                if y <= 0: return 7
                cs = self.colours[y - 1]
                if len(cs) > 0: return cs[-1]
                return find_last_colour_before(y - 1)

            while len(cols) <= self.cursor_x:
                if len(cols) == 0:
                    cols.append(find_last_colour_before(self.cursor_y))
                else:
                    cols.append(cols[-1])
            while len(chrs) <= self.cursor_x:
                chrs += ' '
            cols[self.cursor_x] = self.text_colour
            chrs = chrs[:self.cursor_x] + t + chrs[self.cursor_x + 1:]
            self.text[self.cursor_y] = chrs
            self.colours[self.cursor_y] = cols
            self.cursor_x += 1
        elif type(t) is EscapeSequence:
            if t.command == 'c':
                self.__init__()
            elif t.command == '[m':
                for param in t.params:
                    if param == 0:
                        self.text_colour = 7
                    elif 30 <= param <= 37:
                        self.text_colour = (self.text_colour & ~7) | (param - 30)
                    elif param == 1:
                        self.text_colour |= 8
                    elif param == 2:
                        self.text_colour &= ~8
                    elif 40 <= param <= 47:
                        pass
                    elif param == 7:
                        pass
                    elif param == 27:
                        pass
                    else:
                        raise ValueError('Unexpected param ' + str(param) + '  in SGR code: ' + str(t))

            elif t.command == '[H':
                self.cursor_x = t.params[1] - 1
                self.cursor_y = t.params[0] - 1
            elif t.command == '[A':
                self.cursor_y -= max(1, t.params[0])
                if self.cursor_y < 0:
                    self.cursor_y = 0
            elif t.command == '[D':
                self.cursor_y += max(1, t.params[0])
            elif t.command == '[C':
                self.cursor_x += max(1, t.params[0])
                if self.cursor_x < 0:
                    self.cursor_x = 0
            elif t.command == '[D':
                self.cursor_x -= max(1, t.params[0])
            elif t.command == '[r':
                pass # this has something to do with scrolling, but we do not support this nor we care
            else:
                raise ValueError('Unsupported escape code: ' + str(t))

    def find_all_occurences(self, character: str) -> List[Tuple[int, int]]:
        if len(character) != 1:
            raise ValueError("Can only search for one parameter")
        result = []
        for y, line in enumerate(self.text):
            for x, char in enumerate(line):
                if char == character:
                    result.append((x, y))
        return result

    def parse_rectangle(self, x1: int, y1: int, x2: Optional[int] = None, y2: Optional[int] = None) -> List[
        List[Tuple[int, str]]]:
        if y2 is None:
            y2 = len(self.text)
        result = []
        for y in range(y1, y2):
            tl: str = self.text[y]
            cl: [int] = self.colours[y]
            sub_result: [Tuple[int, str]] = []
            act_x2 = len(tl) if x2 is None else min(x2, len(tl))
            if x1 >= act_x2:
                continue
            curr_colour = cl[x1]
            curr_word = ''
            for x in range(x1, act_x2):
                if tl[x] != ' ' and cl[x] != curr_colour:
                    if curr_word != '' and not curr_word.isspace():
                        sub_result.append((curr_colour, curr_word.strip()))
                    curr_colour = cl[x]
                    curr_word = ''
                curr_word += tl[x]
            if curr_word != '' and not curr_word.isspace():
                sub_result.append((curr_colour, curr_word.strip()))
            result.append(sub_result)
        return result

    def char_at(self, x: int, y: int):
        if y >= len(self.text):
            return ' '
        line = self.text[y]
        if x >= len(line):
            return ' '
        return line[x]

    def find_bordered_rectangle(self) -> Optional[Tuple[int, int, int, int]]:
        # TODO: some rectangles have a horizontal line instead of corner at top left!
        top_lefts = self.find_all_occurences('┌')
        bottom_rights = self.find_all_occurences('┘')
        # print(top_lefts)
        # print(bottom_rights)
        for br in bottom_rights:
            x2 = br[0]
            y2 = br[1]
            for tl in top_lefts:
                x1 = tl[0]
                y1 = tl[1]
                if self.char_at(x1, y2) != '└':
                    continue
                if self.char_at(x2, y1) != '┐':
                    continue
                borders_bad = False
                for x in range(x1 + 1, x2):
                    if self.char_at(x, y1) != '─':
                        borders_bad = True
                    if self.char_at(x, y2) != '─':
                        borders_bad = True
                if borders_bad:
                    continue
                for y in range(y1 + 1, y2):
                    # Ultimate 1541 draws submenus with a dingle-dangle on the left side
                    if self.char_at(x1, y) != '│' and self.char_at(x1, y) != '┐' and self.char_at(x1, y) != '─':
                        borders_bad = True
                    if self.char_at(x2, y) != '│':
                        borders_bad = True
                if borders_bad:
                    continue
                return x1 + 1, y1 + 1, x2, y2
        return None

    def print_all(self):
        for y, line in enumerate(self.text):
            colour_counter: [int] = [0] * 16
            for cl in self.colours[y]:
                colour_counter[cl] += 1
            best_colour = colour_counter.index(max(colour_counter))
            if line.isspace():
                print('n/a ' + line)
            else:
                print(COLOUR_NAMES[best_colour] + ' ' + line)
