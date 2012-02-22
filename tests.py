import os
import shutil
import unittest
import microsearch


class UnhashedMicrosearch(microsearch.Microsearch):
    def hash_name(self, *args, **kwargs):
        # For purposes of testing multiple terms, it's easier if they all
        # go to the same file.
        return 'abc'


class MicrosearchTestCase(unittest.TestCase):
    def setUp(self):
        super(MicrosearchTestCase, self).setUp()
        self.base = os.path.join('/tmp', 'microsearch_tests')
        shutil.rmtree(self.base, ignore_errors=True)

        self.micro = microsearch.Microsearch(self.base)
        self.unhashed_micro = UnhashedMicrosearch(self.base)

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

    def test_hash_name(self):
        self.assertEqual(self.micro.hash_name('hello'), '5d4140')
        self.assertEqual(self.micro.hash_name('world'), '7d7930')
        self.assertEqual(self.micro.hash_name('truly'), 'f499b3')
        self.assertEqual(self.micro.hash_name('splendid'), '291e4e')
        self.assertEqual(self.micro.hash_name('example'), '1a79a4')
        self.assertEqual(self.micro.hash_name('some'), '03d59e')
        self.assertEqual(self.micro.hash_name('tokens'), '25d718')
        self.assertEqual(self.micro.hash_name('top'), 'b28354')
        self.assertEqual(self.micro.hash_name('notch'), '9ce862')
        self.assertEqual(self.micro.hash_name('really'), 'd2d92e')

        self.assertEqual(self.micro.hash_name('notch', length=4), '9ce8')
        self.assertEqual(self.micro.hash_name('really', length=8), 'd2d92eb9')

    def test_make_segment_name(self):
        self.assertEqual(self.micro.make_segment_name('hello'), '/tmp/microsearch_tests/index/5d4140.index')
        self.assertEqual(self.micro.make_segment_name('world'), '/tmp/microsearch_tests/index/7d7930.index')
        self.assertEqual(self.micro.make_segment_name('truly'), '/tmp/microsearch_tests/index/f499b3.index')
        self.assertEqual(self.micro.make_segment_name('splendid'), '/tmp/microsearch_tests/index/291e4e.index')
        self.assertEqual(self.micro.make_segment_name('example'), '/tmp/microsearch_tests/index/1a79a4.index')
        self.assertEqual(self.micro.make_segment_name('some'), '/tmp/microsearch_tests/index/03d59e.index')
        self.assertEqual(self.micro.make_segment_name('tokens'), '/tmp/microsearch_tests/index/25d718.index')
        self.assertEqual(self.micro.make_segment_name('top'), '/tmp/microsearch_tests/index/b28354.index')
        self.assertEqual(self.micro.make_segment_name('notch'), '/tmp/microsearch_tests/index/9ce862.index')
        self.assertEqual(self.micro.make_segment_name('really'), '/tmp/microsearch_tests/index/d2d92e.index')

    def test_parse_record(self):
        self.assertEqual(self.micro.parse_record('hello\t{"abc": [1, 2, 3]}\n'), ['hello', '{"abc": [1, 2, 3]}'])

    def test_make_record(self):
        self.assertEqual(self.micro.make_record('hello', {"abc": [1, 2, 3]}), 'hello\t{"abc": [1, 2, 3]}\n')

    def test_save_segment(self):
        raw_index = self.micro.make_segment_name('hello')
        self.assertFalse(os.path.exists(raw_index))

        self.assertTrue(self.micro.save_segment('hello', {'abc': [1, 5]}))
        self.assertTrue(os.path.exists(raw_index))

        with open(raw_index, 'r') as raw_index_file:
            self.assertEqual(raw_index_file.read(), 'hello\t{"abc": [1, 5]}\n')

        self.assertTrue(self.micro.save_segment('hello', {'abc': [1, 5], 'bcd': [3, 4]}))
        self.assertTrue(os.path.exists(raw_index))

        with open(raw_index, 'r') as raw_index_file:
            self.assertEqual(raw_index_file.read(), 'hello\t{"bcd": [3, 4], "abc": [1, 5]}\n')

    def test_unhashed_save_segment(self):
        raw_index = self.unhashed_micro.make_segment_name('hello')
        self.assertEqual(raw_index, '/tmp/microsearch_tests/index/abc.index')
        self.assertFalse(os.path.exists(raw_index))

        self.assertTrue(self.unhashed_micro.save_segment('hello', {'abc': [1, 5]}))
        self.assertTrue(os.path.exists(raw_index))

        with open(raw_index, 'r') as raw_index_file:
            self.assertEqual(raw_index_file.read(), 'hello\t{"abc": [1, 5]}\n')

        self.assertTrue(self.unhashed_micro.save_segment('hello', {'abc': [1, 5], 'bcd': [3, 4]}))
        self.assertTrue(self.unhashed_micro.save_segment('hell', {'ab': [2]}))
        self.assertTrue(self.unhashed_micro.save_segment('alpha', {'efg': [9, 10]}))
        self.assertTrue(self.unhashed_micro.save_segment('zeta', {'efg': [1, 3]}))
        self.assertTrue(os.path.exists(raw_index))

        with open(raw_index, 'r') as raw_index_file:
            self.assertEqual(raw_index_file.read(), 'alpha\t{"efg": [9, 10]}\nhell\t{"ab": [2]}\nhello\t{"bcd": [3, 4], "abc": [1, 5]}\nzeta\t{"efg": [1, 3]}\n')

    def test_load_segment(self):
        raw_index = self.micro.make_segment_name('hello')
        self.assertFalse(os.path.exists(raw_index))

        # Shouldn't fail if it's not there.
        self.assertEqual(self.micro.load_segment('hello'), {})

        with open(raw_index, 'w') as raw_index_file:
            raw_index_file.write('hello\t{"bcd": [3, 4], "abc": [1, 5]}\n')

        self.assertTrue(os.path.exists(raw_index))

        # Should load the correct term data.
        self.assertEqual(self.micro.load_segment('hello'), {u'abc': [1, 5], u'bcd': [3, 4]})

        # Won't hash to the same file & since we didn't put the data there,
        # it fails to lookup.
        self.assertEqual(self.micro.load_segment('binary'), {})

    def test_unhashed_load_segment(self):
        raw_index = self.unhashed_micro.make_segment_name('hello')
        self.assertFalse(os.path.exists(raw_index))

        # Shouldn't fail if it's not there.
        self.assertEqual(self.unhashed_micro.load_segment('hello'), {})

        with open(raw_index, 'w') as raw_index_file:
            raw_index_file.write('alpha\t{"efg": [9, 10]}\nhell\t{"ab": [2]}\nhello\t{"bcd": [3, 4], "abc": [1, 5]}\nzeta\t{"efg": [1, 3]}\n')

        self.assertTrue(os.path.exists(raw_index))

        # Should load the correct term data.
        self.assertEqual(self.unhashed_micro.load_segment('hello'), {u'abc': [1, 5], u'bcd': [3, 4]})
        self.assertEqual(self.unhashed_micro.load_segment('hell'), {u'ab': [2]})
        self.assertEqual(self.unhashed_micro.load_segment('zeta'), {"efg": [1, 3]})

        # Term miss.
        self.assertEqual(self.unhashed_micro.load_segment('binary'), {})

    def test_make_document_name(self):
        self.assertEqual(self.micro.make_document_name('hello'), '/tmp/microsearch_tests/documents/5d4140/hello.json')
        self.assertEqual(self.micro.make_document_name('world'), '/tmp/microsearch_tests/documents/7d7930/world.json')
        self.assertEqual(self.micro.make_document_name('truly'), '/tmp/microsearch_tests/documents/f499b3/truly.json')
        self.assertEqual(self.micro.make_document_name('splendid'), '/tmp/microsearch_tests/documents/291e4e/splendid.json')
        self.assertEqual(self.micro.make_document_name('example'), '/tmp/microsearch_tests/documents/1a79a4/example.json')
        self.assertEqual(self.micro.make_document_name('some'), '/tmp/microsearch_tests/documents/03d59e/some.json')

    def test_save_document(self):
        raw_doc = self.micro.make_document_name('hello')
        self.assertFalse(os.path.exists(raw_doc))

        self.assertTrue(self.micro.save_document('hello', {'abc': [1, 5]}))
        self.assertTrue(os.path.exists(raw_doc))

        with open(raw_doc, 'r') as raw_doc_file:
            self.assertEqual(raw_doc_file.read(), '{"abc": [1, 5]}')

    def test_load_document(self):
        raw_doc = self.micro.make_document_name('hello')
        self.assertFalse(os.path.exists(raw_doc))
        os.makedirs(os.path.dirname(raw_doc))

        with open(raw_doc, 'w') as raw_doc_file:
            raw_doc_file.write('{"bcd": [3, 4], "abc": [1, 5]}\n')

        self.assertTrue(os.path.exists(raw_doc))

        # Should load the correct document data.
        self.assertEqual(self.micro.load_document('hello'), {u'abc': [1, 5], u'bcd': [3, 4]})

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
        raw_index = self.unhashed_micro.make_segment_name('hello')
        self.assertFalse(os.path.exists(raw_index))

        with open(raw_index, 'w') as raw_index_file:
            raw_index_file.write('alpha\t{"efg": [9, 10]}\nhell\t{"ab": [2]}\nhello\t{"bcd": [3, 4], "abc": [1, 5]}\nzeta\t{"efg": [1, 3]}\n')

        self.assertTrue(os.path.exists(raw_index))

        # Should load the correct term data.
        self.assertEqual(self.unhashed_micro.collect_results(['hello']), {'hello': {u'bcd': [3, 4], u'abc': [1, 5]}})
        self.assertEqual(self.unhashed_micro.collect_results(['hell']), {'hell': {u'ab': [2]}})
        self.assertEqual(self.unhashed_micro.collect_results(['zeta', 'alpha', 'foo']), {'alpha': {u'efg': [9, 10]}, 'foo': {}, 'zeta': {u'efg': [1, 3]}})

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


if __name__ == '__main__':
    unittest.main()
