# -*- coding: utf-8 -*-
from __future__ import unicode_literals
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
