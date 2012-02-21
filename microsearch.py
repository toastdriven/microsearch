"""
microsearch
===========

A small search library.

Primarily intended to be a learning tool to teach the fundamentals of search.

Documents are dictionaries & look like::

    # Keys are field names.
    # Values are the field's contents.
    {
        "id": "document-1524",
        "text": "This is a blob of text. Nothing special about the text, just a typical document.",
        "created": "2012-02-18T20:19:00-0000",
    }

The (inverted) index itself (represented by the segment file bits), is also
essentially a dictionary. The difference is that the index is term-based, unlike
the field-based nature of the document::

    # Keys are terms.
    # Values are document/position information.
    index = {
        'blob': {
            'document-1524': [3],
        },
        'text': {
            'document-1524': [5, 10],
        },
        ...
    }

"""
import hashlib
import json
import math
import os
import re
import tempfile


__author__ = 'Daniel Lindsley'
__license__ = 'BSD'
__version__ = (0, 1, 0)


class Microsearch(object):
    # A fairly standard list of "stopwords", which are words that contribute little
    # to relevance (since they are so common in English) & are to be ignored.
    STOP_WORDS = set([
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'but', 'by',
        'for', 'if', 'in', 'into', 'is', 'it',
        'no', 'not', 'of', 'on', 'or', 's', 'such',
        't', 'that', 'the', 'their', 'then', 'there', 'these',
        'they', 'this', 'to', 'was', 'will', 'with'
    ])
    PUNCTUATION = re.compile('[~`!@#$%^&*()+={\[}\]|\\:;"\',<.>/?]')

    def __init__(self, base_directory):
        self.base_directory = base_directory
        self.index_path = os.path.join(self.base_directory, 'index')
        self.docs_path = os.path.join(self.base_directory, 'documents')
        self.setup()

    def setup(self):
        if not os.path.exists(self.base_directory):
            os.makedirs(self.base_directory)

        if not os.path.exists(self.index_path):
            os.makedirs(self.index_path)

        if not os.path.exists(self.docs_path):
            os.makedirs(self.docs_path)

        return True


    # ==============================
    # Tokenization & Term Generation
    # ==============================

    def make_tokens(self, blob):
        # Kill the punctuation.
        blob = self.PUNCTUATION.sub(' ', blob)
        tokens = []

        # Split on spaces.
        for token in blob.split():
            # Make sure everything is in lowercase & whitespace removed.
            token = token.lower().strip()

            if not token in self.STOP_WORDS:
                tokens.append(token)

        return tokens

    def make_ngrams(self, tokens, min_gram=3, max_gram=6):
        terms = {}

        for position, token in enumerate(tokens):
            for window_length in range(min_gram, min(max_gram + 1, len(token) + 1)):
                # Assuming "front" grams.
                gram = token[:window_length]
                terms.setdefault(gram, [])

                if not position in terms[gram]:
                    terms[gram].append(position)

        return terms


    # ================
    # Segment Handling
    # ================

    def make_segment_name(self, term, length=6):
        # Make sure it's ASCII to appease the hashlib gods.
        term = term.encode('ascii', errors='ignore')
        # We hash & slice the term to get a small-ish number of fields
        # and good distribution between them.
        hashed = hashlib.md5(term).hexdigest()
        return "{0}.index".format(hashed[:length])

    def parse_record(self, line):
        return line.rstrip().split('\t', 1)

    def make_record(self, term, term_info):
        return "{0}\t{1}\n".format(term, json.dumps(term_info))

    def save_segment(self, term, term_info):
        seg_name = self.make_segment_name(term)
        new_seg_file = tempfile.NamedTemporaryFile(delete=False)
        written = False

        with open(seg_name, 'r') as seg_file:
            for line in seg_file:
                seg_term, term_info = self.parse_record(line)

                if not written and seg_term > term:
                    # We're at the alphabetical location & need to insert.
                    new_line = self.make_record(term, term_info)
                    new_seg_file.write(new_line)
                elif seg_term == term:
                    # Overwrite the line for the update.
                    line = self.make_record(term, term_info)

                # Either we haven't reached it alphabetically or we're well-past.
                # Write the line.
                new_seg_file.write(line)

        # Atomically move it into place.
        new_seg_file.close()
        os.rename(new_seg_file.name, seg_name)
        return True

    def load_segment(self, term):
        seg_name = self.make_segment_name(term)

        if not os.path.exists(seg_name):
            return {}

        with open(seg_name, 'r') as seg_file:
            for line in seg_file:
                seg_term, term_info = self.parse_record(line)

                if seg_term == term:
                    # Found it.
                    return json.loads(term_info)

        return {}

    def index(self, doc_id, document):
        pass


    # =========
    # Searching
    # =========

    def parse_query(self, query):
        tokens = self.make_tokens(query)
        return self.make_ngrams(tokens)

    def collect_results(self, terms):
        matches = {}

        for term in terms:
            matches[term] = self.load_segment(term)

        return matches

    def bm25_relevance(self, terms, matches, current_docs, total_docs, b=0, k=1.2):
        score = b

        for term in terms:
            idf = math.log((total_docs - matches[term] + 1) / matches[term]) / math.log(1.0 + total_docs)
            score = score + current_docs[term] * idf / (current_docs[term] + k)

        return 0.5 + score / (2 * len(terms))

    def search(self, query):
        terms = self.parse_query(query)
        results = self.collect_results(terms)
