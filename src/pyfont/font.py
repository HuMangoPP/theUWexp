import pygame as pg
import numpy as np

class Font:
    def __init__(self, path: str, charset: str = 'abcdefghijklmnopqrstuvwxyz1234567890.,;-?!_:+[]'):
        """
        The `Font` class contains utilities for formatting and rendering text on a `pg.Surface`.

        The 'Font' class takes as input:

        * `font`: the font style, as a `pg.Surface`, which contains a single row of characters. Font style should be monospace

        * `charset`: the set of characters, appearing in the same order as the characters in `font`
        """
        self.font = pg.image.load(path).convert()
        self.charset = charset
        self.font_width = self.font.get_width() // len(self.charset)
        self.font_height = self.font.get_height()
        self._load_font()

    def _load_font(self):
        """
        Helper function to load the charmap from the font and charset
        """
        self.char_map = {}
        for i, char in enumerate(self.charset):
            letter = pg.Surface((self.font_width, self.font_height))
            letter.blit(self.font, (-i * self.font_width, 0))
            letter.set_colorkey((255, 255, 255))
            self.char_map[char] = letter
        
    def render(
        self,
        display: pg.Surface,
        text: str,
        xy: tuple,
        colour: tuple | list[tuple],
        width: int,
        style: str = 'topleft',
        box_width: float = 0,
        highlighting: str | None = None,
    ):
        """
        Render text onto a surface.

        * `display`: the `pg.Surface` to render onto

        * `text`: the text to render

        * `xy`: a coordinate of the rendering

        * `colour`: the colour of the text to render, or a list of colours when `highlighting` is not `None`

        * `width`: the width of the monospace for the text to render

        * `style`: one of `[topleft, center]`, which specifies if the font should be rendered from the topleft or the center. Default `topleft`

        * `box_width`: the width of the textbox. Text which overflows over the textbox width will wrap onto the next line. Default 0 (no wrapping)
        
        * `highlighting`: a string of digits corresponding to the index for `colour`, the colour that a particular character should be rendered in. Default `None` (no highlighting)
        """
        scale = width / self.font_width
        height = scale * self.font_height
        xy = np.array(xy)

        lines = self._get_paragraphs(text.lower(), width, box_width)
        char_index = 0
        for y, line in enumerate(lines):
            x = 0
            offset = np.zeros(2)
            if style == 'center':
                num_chars = len(' '.join(line))
                offset = np.array([width * (num_chars / 2), height / 2])
            anchor = xy - offset
            for word in line:
                for char in word:
                    letter = pg.transform.scale_by(self.char_map.get(char, self.char_map['?']), scale)
                    coloured = pg.Surface((width, height))
                    if highlighting is not None:
                        coloured.fill(colour[int(highlighting[char_index])])
                    else:
                        coloured.fill(colour)
                    coloured.blit(letter, (0, 0))
                    coloured.set_colorkey((0, 0, 0))
                    display.blit(coloured, anchor + np.array([x * width, y * height]))

                    x += 1
                    char_index += 1
                x += 1
                char_index += 1

    def char_height(self, width: int) -> int:
        """
        Get the height of a character given a monospace `width`.
        """
        return int(np.ceil(self.font_height * width / self.font_width))

    def text_width(self, text: str, width: int) -> int:
        """
        Get the width of text given the `text` and monospace `width`.
        """
        return len(text) * width

    def text_height(self, text: str, width: int, box_width: int) -> int:
        """
        Get the height of a textbox given the `text`, the monospace `width`, and the textbox `box_width`.
        """
        return self.char_height(width) * len(self._get_paragraphs(text, width, box_width))

    def _get_paragraphs(self, text: str, width: int, box_width: int) -> list[list[str]]:
        """
        Helper function to break down `text` into multiple lines based on the calculations from the monospace `width` and textbox `box_width`.
        """
        if box_width == 0:
            return [text.split()]
        max_chars_per_line = box_width // width
        lines = []
        line = []
        char_counter = 0
        for word in text.split():
            if char_counter + len(word) <= max_chars_per_line:
                char_counter += (len(word) + 1)
                line.append(word)
            else:
                if line:
                    lines.append(line)
                    line = [word]
                    char_counter = len(word) + 1
                else:
                    lines.append([word])
                    line = []
                    char_counter = 0
        if line:
            lines.append(line)
        return lines
