
from random import shuffle, randint

CLOSED_CELL_LABEL = "."
OPEN_CELL_LABEL = " "
DECK_KEY = 1
WHOSE_TURN_KEY = 2
WINNER_KEY = 3
TIE = 1


class _Cell:
    _CLOSED = 0
    _TURNED = 1
    _OPEN = 2

    def __init__(self, symbol):
        self._status = _Cell._CLOSED
        self._symbol = symbol


    def __repr__(self):
        return self.__str__()


    def __str__(self):
        if self._status == _Cell._CLOSED:
            return CLOSED_CELL_LABEL
        elif self._status == _Cell._OPEN:
            return OPEN_CELL_LABEL
        else:
            return self._symbol


    def symbol(self):
        return self._symbol


    def is_playable(self):
        return self._status == _Cell._CLOSED


    def is_same_with(self, other):
        return self._symbol == other._symbol


    def turn(self):
        self._status = _Cell._TURNED


    def close(self):
        self._status = _Cell._CLOSED


    def open(self):
        self._status = _Cell._OPEN



class Game:
    """Contains logic for the match symbols game.

    This game is played by 2 people in turns. There is a deck of symbols and
    initially all symbols are closed. Each player opens 2 cells on her turn.
    If both cells have the same symbol, the player's score is incremented and
    the player open 2 other cells. Otherwise, the player's cells are closed and
    it becomes the other player's turn.

    The game is completed when either one of the players manages to match more
    than half of the symbols, or both match the same number of cells, which is
    a tie.
    """


    def __init__(self, symbols, player1, player2):
        """Initializes the game object with the given parameters.

        Symbols is a string of at least 3 unique characters. player1 and
        player2 are also strings which are different than each other.
        """
        if len(symbols) < 2 or len(symbols) != len(set(iter(symbols))) \
            or not player1 or not player2 or player1 == player2:
            raise ValueError
        symbols = list(iter(symbols))
        self._win_score = len(symbols) // 2 + 1
        symbols = symbols + symbols
        shuffle(symbols)
        self._deck = []
        for symbol in symbols:
            self._deck.append(_Cell(symbol))
        self._player1 = player1
        self._player2 = player2
        self._turn = player2 if randint(0, 1) else player1
        self._prev_cell = None
        self._score1 = 0
        self._score2 = 0


    def peek(self):
        """Returns a tuple of pairs with indices of all closed symbols"""
        view = {}
        for i in range(0, len(self._deck)):
            cell = self._deck[i]
            if cell.is_playable():
                p = view.get(cell.symbol(), -1)
                if p == -1:
                    view[cell.symbol()] = i
                else:
                    view[cell.symbol()] = (p, i)

        return tuple(view.values())


    def whose_turn(self):
        """Returns the player who will play"""
        return self._turn


    def players(self):
        """Returns a tuple of the players"""
        return (self._player1, self._player2)


    def play(self, player, cell_index):
        """Opens the given cell and returns the new status of the game.

        Raises ValueError if it is not the given player's turn,  or the given
        cell is not playable. Only closed cells are playable. Also raises
        IndexError if the given cell index is out of the game deck's bounds.

        Each player makes its moves in turns. Each player opens 2 cells during
        her turn. If those cells have different symbols, the player gets no
        score, its cells are closed, and it becomes  the other player's turn.
        If the cells have the same symbol, then the player's score is increased
        and the player opens 2 other cells.

        The game is completed when either one of the players manages to match
        more than half of the symbols, or both match the same number of cells,
        which is a tie.

        Return values are dictionary object. When the game continues, return
        values contain the deck's view and the current turn with DECK_KEY and
        WHOSE_TURN_KEY respectively. When the game is over, the result is
        present in WINNER_KEY, whose value could be either one of the players
        or the TIE value. Return values always contain scores of the players
        with players as keys and their scores as values.
        """
        if self._turn != player:
            # fail if it is not player's turn
            raise ValueError
        elif not 0 <= cell_index < len(self._deck):
            # fail if the given cell index is out of bounds
            raise IndexError

        cell = self._deck[cell_index]
        if not cell.is_playable():
            # fail if the cell is not closed...
            raise ValueError

        cell.turn()

        if not self._prev_cell:
            # this is the first play of the current turn.
            # just open the cell and return...
            self._prev_cell = cell
            return self._get_deck_info()
        elif cell.is_same_with(self._prev_cell):
            # this is the second play of the current turn
            # and the new cell matches with the previous cell.
            cell.open()
            self._prev_cell.open()
            self._prev_cell = None
            status = self._increment_score()
            # if a status is returned, the game is over...
            if status:
                # the game is no more playable.
                self._turn = None
                # either the current turn wins or it is a tie.
                winner = player if status == player else TIE
                return {
                    WINNER_KEY : winner,
                    self._player1 : self._score1,
                    self._player2 : self._score2
                }
            else:
                # the game is still on...
                return self._get_deck_info()
        else:
            # this is the second play of the current turn
            # and the new cell does not match with the previous cell.
            self._turn = self._get_next_player()
            # first close the previous cell, then create the response,
            # and close the current cell at last. by this way, only
            # the current cell will be displayed.
            self._prev_cell.close()
            self._prev_cell = None
            result = self._get_deck_info()
            cell.close()
            return result


    def _increment_score(self):
        if self._turn == self._player1:
            self._score1 += 1
            if self._score1 == self._win_score:
                return self._player1
        else:
            self._score2 += 1
            if self._score2 == self._win_score:
                return self._player2
        return TIE if self._score1 + self._score2 == len(self._deck) // 2 else 0


    def _get_deck_symbols(self):
        deck_symbols = []
        for symbol in self._deck:
            deck_symbols.append(str(symbol))
        return deck_symbols


    def _get_next_player(self):
        return self._player1 if self._turn == self._player2 else self._player2


    def _get_deck_info(self):
        return {
            DECK_KEY : self._get_deck_symbols(),
            WHOSE_TURN_KEY : self._turn,
            self._player1 : self._score1,
            self._player2 : self._score2
        }
