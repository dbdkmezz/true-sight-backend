class ListNotStartedError(Exception):
    pass


class NoSingularListError(Exception):
    pass


class NoPluralListError(Exception):
    pass


class ParagraphBuilder(object):
    def __init__(self):
        self._current_sentence = None
        self._current_list = None
        self._sentences = []

    def to_string(self):
        self._end_current_sentence()
        return ' '.join(self._sentences)

    def add_sentence(self, sentence):
        sentence = self._sentence_ending_with_punctuation(sentence)
        self._sentences.append(sentence.capitalize())

    def add_clause(self, clause):
        if not self._current_sentence:
            self._current_sentence = clause.capitalize()
        else:
            self._current_sentence += ' {}'.format(clause)

    def start_list(self, singular_introduction, plural_introduction):
        assert not self._current_list
        self._current_list = ListBuilder(singular_introduction, plural_introduction)

    def add_to_list(self, item):
        try:
            self._current_list.add_item(item)
        except AttributeError:
            raise ListNotStartedError
        
    @staticmethod
    def _sentence_ending_with_punctuation(sentence):
        if sentence[-1] in ('.', '!', '?'):
            return sentence
        else:
            return sentence + '.'

    def _end_current_sentence(self):
        if self._current_list:
            self.add_clause(self._current_list.to_string())
            self._current_list = None
        if self._current_sentence:
            self._sentences.append(self._sentence_ending_with_punctuation(self._current_sentence))
            self._current_sentence = None


class ListBuilder(object):
    def __init__(self, singular_introduction, plural_introduction):
        self._singular_introduction = singular_introduction
        self._plural_introduction = plural_introduction
        self._items = []

    def add_item(self, item):
        self._items.append(item)

    def to_string(self):
        assert self._items
        if len(self._items) == 1:
            if not self._singular_introduction:
                raise NoSingularListError
            return '{} {}'.format(self._singular_introduction, self._items[0])
        else:
            if not self._plural_introduction:
                raise NoPluralListError
            self._items[-1] = 'and ' + self._items[-1]
            return '{} {}'.format(
                self._plural_introduction,
                ', '.join(self._items))
