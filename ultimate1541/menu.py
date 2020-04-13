from typing import List, Optional


class MenuItem(object):
    def __init__(self, label: str, annotation: str):
        self.label: str = label
        self.annotation: str = annotation

    def __str__(self):
        if self.annotation == '':
            return self.label
        return self.label + ' ' + self.annotation

class Menu:
    def __init__(self):
        self.items: List[MenuItem] = []
        self.selected: List[int] = []

    def add_item(self, label: str, annotation: str, selected: bool):
        if selected:
            self.selected.append(len(self.items))
        self.items.append(MenuItem(label, annotation))

    def lookup_by_label(self, label: str) -> Optional[int]:
        for ix, it in enumerate(self.items):
            if it.label == label:
                return ix
        return None

    def __str__(self) -> str:
        return str(self.items)

