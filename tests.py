# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import shutil
import unittest
import microsearch


class EnglishTokenizerTestCase(unittest.TestCase):
    def test_init(self):
        et = microsearch.EnglishTokenizer('Hello world!')
        self.assertEqual(et.text, 'hello world!')

    def test_iter(self):
        et = microsearch.EnglishTokenizer('Hello world!')
        self.assertEqual(et.next(), 'hello')
        self.assertEqual(et.next(), 'world')

    def test_all(self):
        et = microsearch.EnglishTokenizer('Hello world!')
        self.assertEqual(list(et), ['hello', 'world'])

    def test_separators_stopwords(self):
        et = microsearch.EnglishTokenizer('Hello world! I\'m like, totally happy to meet you; it\'s my pleasure. Come, sit by the fire...')
        self.assertEqual(list(et), ['hello', 'world', 'i\'m', 'like', 'totally', 'happy', 'meet', 'you', 'it\'s', 'my', 'pleasure', 'come', 'sit', 'fire'])


class EdgeNgramGeneratorTestCase(unittest.TestCase):
    def test_simple_init(self):
        eng = microsearch.EdgeNgramGenerator('Hello')
        self.assertEqual(eng.token, 'Hello')
        self.assertEqual(eng.min_size, 3)
        self.assertEqual(eng.max_size, 15)
        self.assertEqual(eng.side, microsearch.FRONT)

    def test_complex_init(self):
        eng = microsearch.EdgeNgramGenerator('Hello', min_size=8, side=microsearch.BACK)
        self.assertEqual(eng.token, 'Hello')
        self.assertEqual(eng.min_size, 8)
        self.assertEqual(eng.max_size, 15)
        self.assertEqual(eng.side, microsearch.BACK)

    def test_simple_run(self):
        eng = microsearch.EdgeNgramGenerator('Hello')
        self.assertEqual(eng.run(), ['Hel', 'Hell', 'Hello'])

    def test_alternate_gram_size(self):
        eng = microsearch.EdgeNgramGenerator('Hello', min_size=1, max_size=2)
        self.assertEqual(eng.run(), ['H', 'He'])

    def test_gram_size_bigger_than_text(self):
        eng = microsearch.EdgeNgramGenerator('Hello', min_size=8)
        self.assertEqual(eng.run(), ['Hello'])

    def test_simple_back(self):
        eng = microsearch.EdgeNgramGenerator('Hello', side=microsearch.BACK)
        self.assertEqual(eng.run(), ['llo', 'ello', 'Hello'])

    def test_complex_back(self):
        eng = microsearch.EdgeNgramGenerator('Hello', min_size=2, max_size=4, side=microsearch.BACK)
        self.assertEqual(eng.run(), ['lo', 'llo', 'ello'])


class HashedWriterTestCase(unittest.TestCase):
    def setUp(self):
        super(HashedWriterTestCase, self).setUp()
        self.base = '/tmp/hashedwriter'

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)
        super(HashedWriterTestCase, self).tearDown()

    def test_init(self):
        hf_writer = microsearch.HashedWriter(os.path.join(self.base, 'test'))
        self.assertEqual(hf_writer.base_directory, '/tmp/hashedwriter/test')
        self.assertEqual(hf_writer.hash_length, 6)
        self.assertEqual(hf_writer.read_mode, 'r')
        self.assertEqual(hf_writer.write_mode, 'w')

        hf_writer = microsearch.HashedWriter(os.path.join(self.base, 'test2'), hash_length=8, read_mode='rb', write_mode='ab')
        self.assertEqual(hf_writer.base_directory, '/tmp/hashedwriter/test2')
        self.assertEqual(hf_writer.hash_length, 8)
        self.assertEqual(hf_writer.read_mode, 'rb')
        self.assertEqual(hf_writer.write_mode, 'ab')

    def test_check_filesystem(self):
        hf_writer = microsearch.HashedWriter(os.path.join(self.base, 'test'))
        self.assertEqual(hf_writer.base_directory, '/tmp/hashedwriter/test')
        self.assertFalse(os.path.exists(hf_writer.base_directory))
        self.assertTrue(hf_writer.check_filesystem())
        self.assertTrue(os.path.exists(hf_writer.base_directory))

    def test_generate_path(self):
        hf_writer = microsearch.HashedWriter(os.path.join(self.base, 'test'))
        self.assertEqual(hf_writer.generate_path('abc'), ['/tmp/hashedwriter/test/900150', 'abc.txt'])
        self.assertEqual(hf_writer.generate_path('def'), ['/tmp/hashedwriter/test/4ed940', 'def.txt'])

    def test_filepath(self):
        hf_writer = microsearch.HashedWriter(os.path.join(self.base, 'test'))
        self.assertEqual(hf_writer.filepath('abc'), '/tmp/hashedwriter/test/900150/abc.txt')
        self.assertEqual(hf_writer.filepath('def'), '/tmp/hashedwriter/test/4ed940/def.txt')

    def test_load(self):
        os.makedirs('/tmp/hashedwriter/test/900150')

        with open('/tmp/hashedwriter/test/900150/abc.txt', 'w') as test_file:
            test_file.write('Hello world')

        hf_writer = microsearch.HashedWriter(os.path.join(self.base, 'test'))
        self.assertEqual(hf_writer.load('abc'), 'Hello world')
        self.assertRaises(microsearch.NoDocumentError, hf_writer.load, 'ab')

    def test_save(self):
        self.assertFalse(os.path.exists('/tmp/hashedwriter/test/900150/abc.txt'))
        hf_writer = microsearch.HashedWriter(os.path.join(self.base, 'test'))
        hf_writer.save('abc', 'Goodbye cruel world.')
        self.assertTrue(os.path.exists('/tmp/hashedwriter/test/900150/abc.txt'))

        with open('/tmp/hashedwriter/test/900150/abc.txt', 'r') as hf_file:
            self.assertEqual(hf_file.read(), 'Goodbye cruel world.')

    def test_delete(self):
        os.makedirs('/tmp/hashedwriter/test/900150')

        with open('/tmp/hashedwriter/test/900150/abc.txt', 'w') as test_file:
            test_file.write('Hello there, you.')

        hf_writer = microsearch.HashedWriter(os.path.join(self.base, 'test'))
        self.assertTrue(hf_writer.delete('abc'))
        self.assertFalse(os.path.exists('/tmp/hashedwriter/test/900150/abc.txt'))

        self.assertRaises(microsearch.NoDocumentError, hf_writer.delete, 'ab')


class DocumentTestCase(unittest.TestCase):
    def setUp(self):
        super(DocumentTestCase, self).setUp()
        self.base = '/tmp/microsearch/documents'

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)
        super(DocumentTestCase, self).tearDown()

    def test_load(self):
        directory = os.path.join(self.base, '900150')
        os.makedirs(directory)

        with open(os.path.join(directory, 'abc.json'), 'w') as test_file:
            test_file.write('{"text": "Hello world", "count": 5}')

        doc = microsearch.Document(self.base, 'abc')
        self.assertEqual(doc.load().data, {'text': 'Hello world', 'count': 5})
        doc2 = microsearch.Document(self.base, 'ab')
        self.assertRaises(microsearch.NoDocumentError, doc2.load)

    def test_save(self):
        path = os.path.join(self.base, '900150', 'abc.json')
        self.assertFalse(os.path.exists(path))
        doc = microsearch.Document(self.base, 'abc', data={"text": "Goodbye cruel world.", "count": 5})
        doc.save()
        self.assertTrue(os.path.exists(path))

        with open(path, 'r') as doc_file:
            self.assertEqual(doc_file.read(), '{"count": 5, "text": "Goodbye cruel world."}')

    def test_delete(self):
        directory = os.path.join(self.base, '900150')
        os.makedirs(directory)

        with open(os.path.join(directory, 'abc.json'), 'w') as test_file:
            test_file.write('{"text": "Hello world", "count": 5}')

        doc = microsearch.Document(self.base, 'abc')
        self.assertTrue(doc.delete())
        self.assertFalse(os.path.exists(os.path.join(directory, 'abc.json')))

        doc = microsearch.Document(self.base, 'ab')
        self.assertRaises(microsearch.NoDocumentError, doc.delete)


class IndexTestCase(unittest.TestCase):
    def setUp(self):
        super(IndexTestCase, self).setUp()
        self.base = '/tmp/microsearch/index'

    def tearDown(self):
        shutil.rmtree(self.base, ignore_errors=True)
        super(IndexTestCase, self).tearDown()

    def test_load(self):
        index = microsearch.Index(self.base)
        self.assertEqual(index.data, {})
        self.assertEqual(index._loaded, False)
        index.check_filesystem()

        with open(index.filepath, 'w') as raw_index_file:
            raw_index_file.write('hello\t{"abc": [5, 12], "bcd": [1], "ghi": [75, 83, 202]}\n')
            raw_index_file.write('search\t{"xyz": [1, 16]}\n')

        index.load()
        self.assertEqual(index.data, {'search': {'xyz': [1, 16]}, 'hello': {'bcd': [1], 'abc': [5, 12], 'ghi': [75, 83, 202]}})
        self.assertEqual(index._loaded, True)

    def test_save(self):
        index = microsearch.Index(self.base)
        index.data = {'document': {'abc': [4, 16], 'bcd': [1, 5]}, 'search': {'abc': [7]}}
        index._dirty = True
        index.save()

        with open(index.filepath) as raw_index_file:
            raw_index = raw_index_file.read()
            self.assertEqual(raw_index, 'document\t{"bcd": [1, 5], "abc": [4, 16]}\nsearch\t{"abc": [7]}\n')

    def test_delete(self):
        index = microsearch.Index(self.base)
        index.data = {'document': {'abc': [4, 16], 'bcd': [1, 5]}, 'search': {'abc': [7]}}
        index._dirty = True
        index.save()

        self.assertTrue(os.path.exists(index.filepath))

        index.delete()
        self.assertFalse(os.path.exists(index.filepath))

    def test_update(self):
        index = microsearch.Index(self.base)

        # Write a couple.
        index.update('document', 'abc', 5)
        index.update('search', 'abc', 3)
        index.update('document', 'bcd', 12)

        self.assertEqual(index._dirty, True)
        self.assertEqual(index.data, {
            'search': {
                'abc': [3]
            },
            'document': {
                'bcd': [12],
                'abc': [5]
            }
        })

        index.save()

        with open(index.filepath) as raw_index_file:
            raw_index = raw_index_file.read()
            self.assertEqual(raw_index, 'document\t{"bcd": [12], "abc": [5]}\nsearch\t{"abc": [3]}\n')

    def test_get(self):
        index = microsearch.Index(self.base)

        # Write a couple.
        index.update('document', 'abc', 5)
        index.update('search', 'abc', 3)
        index.update('document', 'bcd', 12)
        index.save()

        self.assertEqual(index.get('document'), {'bcd': [12], 'abc': [5]})
        self.assertEqual(index.get('search'), {'abc': [3]})
        self.assertEqual(index.get('pony'), {})

    def test_remove(self):
        index = microsearch.Index(self.base)

        # Write a couple.
        index.update('document', 'abc', 5)
        index.update('search', 'abc', 3)
        index.update('document', 'bcd', 12)
        index.save()

        # Remove one.
        index.remove('document', 'abc', 5)
        self.assertEqual(index.data, {'search': {'abc': [3]}, 'document': {'bcd': [12]}})

        # Remove the other.
        index.remove('document', 'bcd', 12)
        self.assertEqual(index.data, {'search': {'abc': [3]}})

        index.update('document', 'abc', 5)
        index.update('search', 'abc', 3)
        index.update('document', 'bcd', 12)
        index.save()

        # Remove the document.
        index.remove('document', 'bcd')
        self.assertEqual(index.data, {'search': {'abc': [3]}, 'document': {'abc': [5]}})

        # Remove non-existent.
        index.remove('search', 'bcd')
        self.assertEqual(index.data, {'search': {'abc': [3]}, 'document': {'abc': [5]}})

        # Remove the whole term.
        index.remove('document')
        self.assertEqual(index.data, {'search': {'abc': [3]}})

        index.remove('search')
        self.assertEqual(index.data, {})

        # Remove non-existent term
        index.remove('foo')
        self.assertEqual(index.data, {})


class BM25RelevanceTestCase(unittest.TestCase):
    def test_calculations(self):
        bm25 = microsearch.BM25Relevance()

        terms = ['hello']
        matching_docs = {
            'hello': 7,
        }
        current_doc_occurances = {
            'hello': 3,
        }
        total_docs = 17
        self.assertAlmostEqual(bm25.calculate(terms, matching_docs, current_doc_occurances, total_docs), 0.5)

        terms = ['hello']
        matching_docs = {
            'hello': 25,
        }
        current_doc_occurances = {
            'hello': 5,
        }
        total_docs = 175
        self.assertAlmostEqual(bm25.calculate(terms, matching_docs, current_doc_occurances, total_docs), 0.6397323070026185)

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
        self.assertAlmostEqual(bm25.calculate(terms, matching_docs, current_doc_occurances, total_docs), 0.679625629230611)
