# Python 3 compatibility.
from __future__ import print_function
from __future__ import unicode_literals

import os

try:
    import simplejson as json
except ImportError:
    import json


__author__ = 'Daniel Lindsley'
__license__ = 'BSD'
__version__ = (0, 1, 0)


FRONT = 'front'
BACK = 'back'


class EnglishTokenizer(object):
    separators = set([
        '\n', '\r', ' ', '~', '`', '!', '@', '#', '$', '%', '^', '&', '*', '(',
        ')', '+', '=', '{', '[', '}', ']', '|', '\\', ':', ';', '"', '<', ',',
        '>', '.', '?', '/',
        # Leaving these alone, as they commonly combine words.
        # '_', '-', '\'',
    ])
    stopwords = set([
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'but', 'by',
        'for', 'if', 'in', 'into', 'is', 'it',
        'no', 'not', 'of', 'on', 'or', 's', 'such',
        't', 'that', 'the', 'their', 'then', 'there', 'these',
        'they', 'this', 'to', 'was', 'will', 'with'
    ])

    def __init__(self, text):
        self.text = text.lower()
        self.offset = -1

    def __iter__(self):
        current_token = []

        for letter in self.text:
            if letter in self.separators:
                if len(current_token):
                    token = ''.join(current_token)

                    if not token in self.stopwords:
                        yield token

                # Reset the current token to nothing
                current_token = []
            else:
                current_token.append(letter)

        raise StopIteration()

    def next(self):
        for offset, token in enumerate(self):
            if offset > self.offset:
                self.offset = offset
                return token


class EdgeNgramGenerator(object):
    def __init__(self, token, min_size=3, max_size=15, side=FRONT):
        self.token = token
        self.min_size = min_size
        self.max_size = max_size
        self.side = side

    def run(self):
        text = self.token
        grams = []
        length = len(text)

        for slice_len in range(self.min_size, self.max_size + 1):
            if self.side == FRONT:
                current_gram = text[:slice_len]
            else:
                current_gram = text[length - slice_len:]

            if len(current_gram) < slice_len:
                # We've got all the grams covered.
                break

            grams.append(current_gram)

        # If we haven't got any grams but there was valid text there, we have
        # text that was smaller than the ``min_size``. Toss the whole thing
        # into the ``grams`` so the word doesn't get skipped.
        if not grams and length:
            grams.append(text)

        return grams

