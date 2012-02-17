# Python 3 compatibility.
from __future__ import print_function
from __future__ import unicode_literals

import hashlib
import os
import shutil
import tempfile

try:
    import simplejson as json
except ImportError:
    import json


__author__ = 'Daniel Lindsley'
__license__ = 'BSD'
__version__ = (0, 2, 0)


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
        md5 = hashlib.md5(filename.encode('ascii', errors='ignore')).hexdigest()[:self.hash_length]
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


class Index(object):
    """
    TBD.

    Data format is structured like::

        <term>\t<JSON-encoded dictionary of document names, with position lists as values>\n

    Sample data looks like::

        hello\t{'abc': [5, 12], 'bcd': [1], 'ghi': [75, 83, 202]}\n
    """
    def __init__(self, base_directory, name='main'):
        self.base_directory = os.path.join(base_directory, 'index')
        self.name = name
        self.filepath = os.path.join(self.base_directory, name)
        self.data = {}
        self._loaded = False
        self._dirty = False

    def check_filesystem(self):
        if not os.path.exists(self.base_directory):
            os.makedirs(self.base_directory)

        return True

    def parse_record(self, record):
        return record.rstrip().split('\t', 1)

    def parse_term_info(self, raw_term_info):
        return json.loads(raw_term_info)

    def build_record(self, term, term_info):
        return "{0}\t{1}\n".format(term, self.build_term_info(term_info))

    def build_term_info(self, term_info):
        return json.dumps(term_info)

    def load(self):
        self.check_filesystem()

        if not os.path.exists(self.filepath):
            self.data = {}
            self._loaded = True
            return True

        with open(self.filepath, 'r') as index_file:
            for line in index_file:
                term, term_info = self.parse_record(line)
                self.data[term] = self.parse_term_info(term_info)

        self._loaded = True
        self._dirty = False
        return True

    def save(self):
        # If we haven't been modified, just return.
        if not self._dirty:
            return False

        self.check_filesystem()

        # Write a tempfile & move it into place once it's done.
        # FIXME: Eventually, some locking may be needed.
        new_index = tempfile.NamedTemporaryFile(mode='w', delete=False)

        for term in sorted(self.data.keys()):
            new_index.write(self.build_record(term, self.data[term]))

        new_index.close()
        shutil.move(new_index.name, self.filepath)
        self._dirty = False
        return True

    def delete(self):
        try:
            os.unlink(self.filepath)
        except OSError:
            pass

        self._dirty = True
        return True

    def check_term(self, term, document_name=None):
        if not self._loaded:
            self.load()

        self.data.setdefault(term, {})

        if document_name:
            self.data[term].setdefault(document_name, [])

        return True

    def cleanup_term(self, term, document_name=None):
        if document_name and not len(self.data[term][document_name]):
            del(self.data[term][document_name])

        if not len(self.data[term]):
            del(self.data[term])

        return True

    def get(self, term):
        if not self._loaded:
            self.load()

        return self.data.get(term, {})

    def update(self, term, document_name, position):
        self.check_term(term, document_name)

        if not position in self.data[term][document_name]:
            self.data[term][document_name] = sorted(self.data[term][document_name] + [position])

        self._dirty = True
        return True

    def remove(self, term, document_name=None, position=None):
        self.check_term(term, document_name)

        # Just a specific position.
        if document_name is not None and position is not None:
            try:
                offset = self.data[term][document_name].index(position)
                self.data[term][document_name].pop(offset)
                self.cleanup_term(term, document_name)
            except ValueError:
                return False

            self._dirty = True
            return True

        # Just remove a document.
        if document_name is not None:
            try:
                del(self.data[term][document_name])
                self.cleanup_term(term)
            except KeyError:
                return False

            self._dirty = True
            return True

        # Remove the whole term.
        try:
            del(self.data[term])
        except KeyError:
            return False

        self._dirty = True
        return True



# TODO:
# * Index object
#   * Query object
#   * QueryParser object
