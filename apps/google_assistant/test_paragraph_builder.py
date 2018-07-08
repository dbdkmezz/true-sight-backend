from django.test import TestCase

from .paragraph_builder import ParagraphBuilder, ListBuilder, ListNotStartedError, NoSingularListError, NoPluralListError


class TestParagraphBuilder(TestCase):
    def test_single_sentence(self):
        builder = ParagraphBuilder()
        builder.add_sentence('hello world')
        result = builder.to_string()
        assert result == 'Hello world.'

    def test_two_sentences(self):
        builder = ParagraphBuilder()
        builder.add_sentence('hello')
        builder.add_sentence('world')
        result = builder.to_string()
        assert result == 'Hello. World.'

    def test_clauses(self):
        builder = ParagraphBuilder()
        builder.add_clause('hello')
        builder.add_clause('world')
        result = builder.to_string()
        assert result == 'Hello world.'

    def test_singular_list(self):
        builder = ParagraphBuilder()
        builder.add_clause('the best')
        builder.start_list('pizza is', 'pizzas are')
        builder.add_to_list('Hawaiian')
        result = builder.to_string()
        assert result == 'The best pizza is Hawaiian.'

    def test_plural_list(self):
        builder = ParagraphBuilder()
        builder.add_clause('the best')
        builder.start_list('pizza is', 'pizzas are')
        builder.add_to_list('Hawaiian')
        builder.add_to_list('Margherita')
        builder.add_to_list('Pizza Napoli')
        result = builder.to_string()
        assert result == 'The best pizzas are Hawaiian, Margherita, and Pizza Napoli.'
        
    def test_throws_if_list_not_started(self):
        builder = ParagraphBuilder()
        with self.assertRaises(ListNotStartedError):
            builder.add_to_list('Pizza')


class TestListBuilder(TestCase):
    def test_raises_if_no_singular_option(self):
        builder = ListBuilder(None, 'pizzas are')
        builder.add_item('Hawaiian')
        with self.assertRaises(NoSingularListError):
            builder.to_string()

    def test_raises_if_no_plural_option(self):
        builder = ListBuilder('pizza is', None)
        builder.add_item('Hawaiian')
        builder.add_item('Margherita')
        with self.assertRaises(NoPluralListError):
            builder.to_string()
