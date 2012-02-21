import os
import shutil
import unittest
import microsearch


class MicrosearchTestCase(unittest.TestCase):
    def setUp(self):
        super(MicrosearchTestCase, self).setUp()
        self.base = os.path.join('/tmp', 'microsearch_tests')
        shutil.rmtree(self.base, ignore_errors=True)

        self.micro = microsearch.Microsearch(self.base)

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)
        super(MicrosearchTestCase, self).tearDown()

    def test_make_tokens(self):
        self.assertEqual(self.micro.make_tokens('Hello world'), ['hello', 'world'])
        self.assertEqual(self.micro.make_tokens("This is a truly splendid example of some tokens. Top notch, really."), ['truly', 'splendid', 'example', 'some', 'tokens', 'top', 'notch', 'really'])

    def test_make_ngrams(self):
        self.assertEqual(self.micro.make_ngrams(['hello', 'world']), {
            'hel': [0],
            'hell': [0],
            'hello': [0],
            'wor': [1],
            'worl': [1],
            'world': [1],
        })
        self.assertEqual(self.micro.make_ngrams(['truly', 'splendid', 'example', 'some', 'tokens', 'top', 'notch', 'really']), {
            'tru': [0],
            'trul': [0],
            'truly': [0],
            'spl': [1],
            'sple': [1],
            'splen': [1],
            'splend': [1],
            'exa': [2],
            'exam': [2],
            'examp': [2],
            'exampl': [2],
            'som': [3],
            'some': [3],
            'tok': [4],
            'toke': [4],
            'token': [4],
            'tokens': [4],
            'top': [5],
            'not': [6],
            'notc': [6],
            'notch': [6],
            'rea': [7],
            'real': [7],
            'reall': [7],
            'really': [7],
        })

    def test_make_segment_name(self):
        self.assertEqual(self.micro.make_segment_name('hello'), '5d4140.index')
        self.assertEqual(self.micro.make_segment_name('world'), '7d7930.index')
        self.assertEqual(self.micro.make_segment_name('truly'), 'f499b3.index')
        self.assertEqual(self.micro.make_segment_name('splendid'), '291e4e.index')
        self.assertEqual(self.micro.make_segment_name('example'), '1a79a4.index')
        self.assertEqual(self.micro.make_segment_name('some'), '03d59e.index')
        self.assertEqual(self.micro.make_segment_name('tokens'), '25d718.index')
        self.assertEqual(self.micro.make_segment_name('top'), 'b28354.index')
        self.assertEqual(self.micro.make_segment_name('notch'), '9ce862.index')
        self.assertEqual(self.micro.make_segment_name('really'), 'd2d92e.index')

    def test_parse_record(self):
        self.assertEqual(self.micro.parse_record('hello\t{"abc": [1, 2, 3]}\n'), ['hello', '{"abc": [1, 2, 3]}'])

    def test_make_record(self):
        self.assertEqual(self.micro.make_record('hello', {"abc": [1, 2, 3]}), 'hello\t{"abc": [1, 2, 3]}\n')

    def test_save_segment(self):
        pass

    def test_load_segment(self):
        pass

    def test_parse_query(self):
        self.assertEqual(self.micro.parse_query('Hello world!'), {
            'hel': [0],
            'hell': [0],
            'hello': [0],
            'wor': [1],
            'worl': [1],
            'world': [1],
        })

    def test_collect_results(self):
        pass

    def test_bm25_relevance(self):
        terms = ['hello']
        matching_docs = {
            'hello': 7,
        }
        current_doc_occurances = {
            'hello': 3,
        }
        total_docs = 17
        relevance = self.micro.bm25_relevance(terms, matching_docs, current_doc_occurances, total_docs)
        self.assertEqual("{:.2f}".format(relevance), '0.56', 'This fails on 2.X but should pass on Python 3.')

        terms = ['hello']
        matching_docs = {
            'hello': 25,
        }
        current_doc_occurances = {
            'hello': 5,
        }
        total_docs = 175
        relevance = self.micro.bm25_relevance(terms, matching_docs, current_doc_occurances, total_docs)
        self.assertEqual("{:.2f}".format(relevance), '0.64', 'This fails on 2.X but should pass on Python 3.')

        terms = ['hello', 'world']
        matching_docs = {
            'hello': 25,
            'world': 7,
        }
        current_doc_occurances = {
            'hello': 5,
            'world': 3,
        }
        total_docs = 175
        relevance = self.micro.bm25_relevance(terms, matching_docs, current_doc_occurances, total_docs)
        self.assertEqual("{:.2f}".format(relevance), '0.68', 'This fails on 2.X but should pass on Python 3.')
