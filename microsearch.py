# Python 3 compatibility.
from __future__ import print_function
from __future__ import unicode_literals

import hashlib
import os
import shutil

try:
    import simplejson as json
except ImportError:
    import json


__author__ = 'Daniel Lindsley'
__license__ = 'BSD'
__version__ = (0, 1, 0)


FRONT = 'front'
BACK = 'back'


class MicrosearchError(Exception): pass
class DataError(MicrosearchError): pass
class NoDocumentError(MicrosearchError): pass


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


class HashedWriter(object):
    def __init__(self, base_directory, hash_length=6, read_mode='r', write_mode='w', extension='txt'):
        self.base_directory = base_directory
        self.hash_length = hash_length
        self.read_mode = read_mode
        self.write_mode = write_mode
        self.extension = extension

    def check_filesystem(self, path=None):
        if not os.path.exists(self.base_directory):
            os.makedirs(self.base_directory)

        if path:
            if not os.path.exists(path):
                os.makedirs(path)

        return True

    def generate_path(self, filename):
        # We hash the doc_id to ensure that there are
        # never too many files in a directory.
        md5 = hashlib.md5(filename).hexdigest()[:self.hash_length]
        filename = "{0}.{1}".format(filename, self.extension)
        return [os.path.join(self.base_directory, md5), filename]

    def filepath(self, filename):
        path, filename = self.generate_path(filename)
        self.check_filesystem(path)
        return os.path.join(path, filename)

    def load(self, filename):
        hf_filepath = self.filepath(filename)

        try:
            with open(hf_filepath, self.read_mode) as hf_file:
                return hf_file.read()
        except IOError as e:
            raise NoDocumentError("Couldn't load '%s': %s" % (hf_filepath, e))

    def save(self, filename, data):
        hf_filepath = self.filepath(filename)

        with open(hf_filepath, self.write_mode) as hf_file:
            hf_file.write(data)

        return True

    def delete(self, filename):
        hf_filepath = self.filepath(filename)

        try:
            os.unlink(hf_filepath)
        except OSError as e:
            raise NoDocumentError("Couldn't delete '%s': %s" % (hf_filepath, e))

        return True


class Document(object):
    def __init__(self, base_directory, doc_id, data=None, default_field='text', writer=None):
        self.base_directory = os.path.join(base_directory, 'docs')
        self.doc_id = doc_id
        self.data = data or {}
        self.default_field = default_field
        self.writer = writer

        if not self.writer:
            self.writer = HashedWriter(base_directory, extension='json')

        if len(self.data) and not default_field in self.data:
            raise DataError("The default field '%s' is not present in the provided data." % self.default_field)

    def load(self):
        data = self.writer.load(self.doc_id)
        self.data = json.loads(data)
        return self

    def save(self):
        return self.writer.save(self.doc_id, json.dumps(self.data))

    def delete(self):
        return self.writer.delete(self.doc_id)


# TODO:
# * Index object
#   * Segment object
#   * Query object
#   * QueryParser object
