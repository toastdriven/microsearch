import json
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

    def test_read_stats(self):
        # No file.
        self.assertFalse(os.path.exists(self.micro.stats_path))
        self.assertEqual(self.micro.read_stats(), {'total_docs': 0, 'version': '.'.join([str(bit) for bit in microsearch.__version__])})

        with open(self.micro.stats_path, 'w') as stats_file:
            json.dump({
                'version': '0.7.0'
            }, stats_file)

        self.assertEqual(self.micro.read_stats(), {'version': '0.7.0'})

    def test_write_stats(self):
        # No file.
        self.assertFalse(os.path.exists(self.micro.stats_path))
        self.assertTrue(self.micro.write_stats({
            'version': '0.8.0',
            'total_docs': 15,
        }))
        self.assertTrue(os.path.exists(self.micro.stats_path))

        with open(self.micro.stats_path, 'r') as stats_file:
            self.assertEqual(json.load(stats_file), {'total_docs': 15, 'version': '0.8.0'})

    def test_increment_total_docs(self):
        self.assertTrue(self.micro.write_stats({
            'version': '0.8.0',
            'total_docs': 15,
        }))

        self.micro.increment_total_docs()
        self.micro.increment_total_docs()
        self.micro.increment_total_docs()

        self.assertEqual(self.micro.read_stats(), {'total_docs': 18, 'version': '0.8.0'})

    def test_get_total_docs(self):
        self.assertTrue(self.micro.write_stats({
            'version': '0.8.0',
            'total_docs': 12,
        }))

        self.assertEqual(self.micro.get_total_docs(), 12)

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
        path_prefix = os.path.join('/tmp', 'microsearch_tests', 'index')
        self.assertEqual(self.micro.make_segment_name('hello'), os.path.join(path_prefix,'5d4140.index' ))
        self.assertEqual(self.micro.make_segment_name('world'), os.path.join(path_prefix, '7d7930.index'))
        self.assertEqual(self.micro.make_segment_name('truly'), os.path.join(path_prefix, 'f499b3.index'))
        self.assertEqual(self.micro.make_segment_name('splendid'), os.path.join(path_prefix, '291e4e.index'))
        self.assertEqual(self.micro.make_segment_name('example'), os.path.join(path_prefix, '1a79a4.index'))
        self.assertEqual(self.micro.make_segment_name('some'), os.path.join(path_prefix, '03d59e.index'))
        self.assertEqual(self.micro.make_segment_name('tokens'), os.path.join(path_prefix, '25d718.index'))
        self.assertEqual(self.micro.make_segment_name('top'), os.path.join(path_prefix, 'b28354.index'))
        self.assertEqual(self.micro.make_segment_name('notch'), os.path.join(path_prefix, '9ce862.index'))
        self.assertEqual(self.micro.make_segment_name('really'), os.path.join(path_prefix, 'd2d92e.index'))

    def test_parse_record(self):
        self.assertEqual(self.micro.parse_record('hello\t{"abc": [1, 2, 3]}\n'), ['hello', '{"abc": [1, 2, 3]}'])

    def test_make_record(self):
        self.assertEqual(self.micro.make_record('hello', {"abc": [1, 2, 3]}), 'hello\t{"abc": [1, 2, 3]}\n')

    def test_update_term_info(self):
        orig = {
            "abc": [1, 2, 3],
            "ab": [2],
        }
        new = {
            "abc": [2, 1, 5],
            "bcd": [2, 3],
            "ghi": [25],
        }
        self.assertEqual(self.micro.update_term_info(orig, new), {
            'ab': [2],
            'abc': [1, 2, 3, 5],
            'bcd': [2, 3],
            'ghi': [25]
        })

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
        goal_path = os.path.join('/tmp', 'microsearch_tests', 'index', 'abc.index')
        self.assertEqual(raw_index, goal_path)
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
        self.assertEqual(self.micro.load_segment('hello'), {'abc': [1, 5], 'bcd': [3, 4]})

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
        self.assertEqual(self.unhashed_micro.load_segment('hello'), {'abc': [1, 5], 'bcd': [3, 4]})
        self.assertEqual(self.unhashed_micro.load_segment('hell'), {'ab': [2]})
        self.assertEqual(self.unhashed_micro.load_segment('zeta'), {"efg": [1, 3]})

        # Term miss.
        self.assertEqual(self.unhashed_micro.load_segment('binary'), {})

    def test_make_document_name(self):
        path_prefix = os.path.join('/tmp', 'microsearch_tests', 'documents')
        self.assertEqual(self.micro.make_document_name('hello'), os.path.join(path_prefix,'5d4140', 'hello.json'))
        self.assertEqual(self.micro.make_document_name('world'), os.path.join(path_prefix, '7d7930','world.json'))
        self.assertEqual(self.micro.make_document_name('truly'), os.path.join(path_prefix, 'f499b3', 'truly.json'))
        self.assertEqual(self.micro.make_document_name('splendid'), os.path.join(path_prefix, '291e4e', 'splendid.json'))
        self.assertEqual(self.micro.make_document_name('example'), os.path.join(path_prefix, '1a79a4', 'example.json'))
        self.assertEqual(self.micro.make_document_name('some'), os.path.join(path_prefix, '03d59e', 'some.json'))

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
        self.assertEqual(self.micro.load_document('hello'), {'abc': [1, 5], 'bcd': [3, 4]})

    def test_index(self):
        # Check the exceptions.
        self.assertRaises(AttributeError, self.micro.index, 'email_1', 'A raw doc.')
        self.assertRaises(KeyError, self.micro.index, 'email_1', {'subject': 'A raw doc.'})

        doc_1 = self.unhashed_micro.index('email_1', {'text': "Peter,\n\nI'm going to need those TPS reports on my desk first thing tomorrow! And clean up your desk!\n\nLumbergh"})
        doc_2 = self.unhashed_micro.index('email_2', {'text': 'Everyone,\n\nM-m-m-m-my red stapler has gone missing. H-h-has a-an-anyone seen it?\n\nMilton'})
        doc_3 = self.unhashed_micro.index('email_3', {'text': "Peter,\n\nYeah, I'm going to need you to come in on Saturday. Don't forget those reports.\n\nLumbergh"})
        doc_4 = self.unhashed_micro.index('email_4', {'text': 'How do you feel about becoming Management?\n\nThe Bobs'})

        self.assertTrue(doc_1)
        self.assertTrue(doc_2)
        self.assertTrue(doc_3)
        self.assertTrue(doc_4)

        raw_doc_1 = self.unhashed_micro.make_document_name('email_1')
        self.assertTrue(os.path.exists(raw_doc_1))
        raw_doc_2 = self.unhashed_micro.make_document_name('email_2')
        self.assertTrue(os.path.exists(raw_doc_2))
        raw_doc_3 = self.unhashed_micro.make_document_name('email_3')
        self.assertTrue(os.path.exists(raw_doc_3))
        raw_doc_4 = self.unhashed_micro.make_document_name('email_4')
        self.assertTrue(os.path.exists(raw_doc_4))

        with open(raw_doc_1, 'r') as raw_doc_file_1:
            self.assertEqual(raw_doc_file_1.read(), '{"text": "Peter,\\n\\nI\'m going to need those TPS reports on my desk first thing tomorrow! And clean up your desk!\\n\\nLumbergh"}')

        raw_index = self.unhashed_micro.make_segment_name('peter')
        self.assertTrue(os.path.exists(raw_index))

        with open(raw_index, 'r') as raw_index_file_1:
            lines = raw_index_file_1.readlines()

            self.assertEqual(lines[0], 'a-a\t{"email_2": [8]}\n')
            self.assertEqual(lines[1], 'a-an\t{"email_2": [8]}\n')
            self.assertEqual(lines[19], 'desk\t{"email_1": [9, 16]}\n')
            self.assertEqual(lines[74], 'report\t{"email_3": [12], "email_1": [7]}\n')

        self.assertEqual(self.micro.get_total_docs(), 4)

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
        self.assertEqual(self.unhashed_micro.collect_results(['hello']), ({'hello': 2}, {'bcd': {'hello': 2}, 'abc': {'hello': 2}}))
        self.assertEqual(self.unhashed_micro.collect_results(['hell']), ({'hell': 1}, {'ab': {'hell': 1}}))
        self.assertEqual(self.unhashed_micro.collect_results(['zeta', 'alpha', 'foo']), ({'alpha': 1, 'zeta': 1, 'foo': 0}, {'efg': {'alpha': 2, 'zeta': 2}}))

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

    def test_search(self):
        # No query, no results.
        self.assertEqual(self.micro.search(''), {'total_hits': 0, 'results': []})

        # Query, but no documents.
        self.assertEqual(self.micro.search('hello'), {'total_hits': 0, 'results': []})

        # Index some data.
        self.micro.index('email_1', {'text': "Peter,\n\nI'm going to need those TPS reports on my desk first thing tomorrow! And clean up your desk!\n\nLumbergh"})
        self.micro.index('email_2', {'text': 'Everyone,\n\nM-m-m-m-my red stapler has gone missing. H-h-has a-an-anyone seen it?\n\nMilton'})
        self.micro.index('email_3', {'text': "Peter,\n\nYeah, I'm going to need you to come in on Saturday. Don't forget those reports.\n\nLumbergh"})
        self.micro.index('email_4', {'text': 'How do you feel about becoming Management?\n\nThe Bobs'})

        # Single term queries.
        self.assertEqual(self.micro.search('peter'), {
            'total_hits': 2,
            'results': [
                {
                    'text': "Peter,\n\nYeah, I'm going to need you to come in on Saturday. Don't forget those reports.\n\nLumbergh",
                    'score': 0.5572567355483165,
                    'id': 'email_3'
                },
                {
                    'text': "Peter,\n\nI'm going to need those TPS reports on my desk first thing tomorrow! And clean up your desk!\n\nLumbergh",
                    'score': 0.5572567355483165,
                    'id': 'email_1'
                }
            ]
        })
        self.assertEqual(self.micro.search('desk'), {
            'total_hits': 1,
            'results': [
                {
                    'text': "Peter,\n\nI'm going to need those TPS reports on my desk first thing tomorrow! And clean up your desk!\n\nLumbergh",
                    'score': 0.7691728487958707,
                    'id': 'email_1'
                }
            ]
        })
        self.assertEqual(self.micro.search('you'), {
            'total_hits': 3,
            'results': [
                {
                    'text': "Peter,\n\nYeah, I'm going to need you to come in on Saturday. Don't forget those reports.\n\nLumbergh",
                    'score': 0.44274326445168355,
                    'id': 'email_3'
                },
                {
                    'text': "Peter,\n\nI'm going to need those TPS reports on my desk first thing tomorrow! And clean up your desk!\n\nLumbergh",
                    'score': 0.44274326445168355,
                    'id': 'email_1'
                },
                {
                    'text': 'How do you feel about becoming Management?\n\nThe Bobs',
                    'score': 0.44274326445168355,
                    'id': 'email_4'
                }
            ]
        })

        # No matches:
        self.assertEqual(self.micro.search('wunderkind'), {'total_hits': 0, 'results': []})

        # Multiple term queries.
        self.assertEqual(self.micro.search('peter desk'), {
            'total_hits': 2,
            'results': [
                {
                    'text': "Peter,\n\nI'm going to need those TPS reports on my desk first thing tomorrow! And clean up your desk!\n\nLumbergh",
                    'score': 0.6420231808473381,
                    'id': 'email_1'
                },
                {
                    'text': "Peter,\n\nYeah, I'm going to need you to come in on Saturday. Don't forget those reports.\n\nLumbergh",
                    'score': 0.5343540413289899,
                    'id': 'email_3'
                }
            ]
        })


if __name__ == '__main__':
    unittest.main()
