from typing import List


class EscapeSequence:
    def __init__(self, command: str, params: List[int]):
        self.command: str = command
        self.params: [int] = params

    def __str__(self):
        if len(self.command) == 2:
            return 'ESC ' + self.command[0] + ';'.join(map(str, self.params)) + self.command[1]
        else:
            return 'ESC ' + self.command + ';'.join(map(str, self.params)) # ???
