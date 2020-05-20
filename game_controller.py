
from game import Game, CLOSED_CELL_LABEL, WINNER_KEY, DECK_KEY, WHOSE_TURN_KEY, TIE
# from string import ascii_lowercase, ascii_uppercase
# from random import shuffle
import random, string



RESET_TERMINAL_CODE = "\033[F\033[K"
GAME_OVER_KEY = 1

_RESET_LINE_CODE = "\033[K"
_INPUT_PROMPT = "enter coordinates (for instance, 1A): "
_WAIT_MESSAGE = "waiting for your opponent to play"
_ROW_LABELS = list(map(str, list(range(1, 10))))
_COL_LABELS = list(string.ascii_uppercase)


def _to_col(ch, limit):
    if ord('a') <= ord(ch) <= ord('z'):   # ord(a) = 97
        num = ord(ch) - ord('a')
    elif ord("A") <= ord(ch) <= ord('Z'): # ord(A) = 65
        num = ord(ch) - ord('A')
    else:
        raise ValueError

    if num >= limit:
        raise ValueError
    return num


def _to_row(ch, limit):
    if ord("1") <= ord(ch) <= ord('9'): # ord(1) = 49
        num = ord(ch) - ord('1')
    else:
        raise ValueError

    if num >= limit:
        raise ValueError
    return num


def _to_index(num_rows, num_cols, row_ch, col_ch):
    return _to_row(row_ch, num_rows) * num_cols + _to_col(col_ch, num_cols)    



class GameController:
    """Receives inputs from players, applies them on the game and returns
    views for users."""

    def __init__(self, num_rows, num_cols, player1, player2):
        """Initializes the controller object with the given parameters.

        The match symbols game deck is displayed in a matrix with an even 
        number of cells. Each cell is a letter in the English alphabet and each
        symbol is placed twice, hence there can be at most 52 cells. Moreover, 
        there can be at most 9 rows and 26 columns, because rows are labeled 
        from 1 to 9 and columns are labeled from A to Z.
        """
        if not 1 <= num_rows <= 9 or not 1 <= num_cols <= 26 \
                or num_rows * num_cols > 52 or num_rows * num_cols // 2 == 1:
            raise ValueError
        self._num_rows = num_rows
        self._num_cols = num_cols
        symbols = list(iter(string.ascii_lowercase))
        random.shuffle(symbols)
        symbols = "".join(symbols[:num_rows * num_cols // 2])
        self._game = Game(symbols, player1, player2)
        self._initial_views = {
            player1 : self._generate_initial_view(player1),
            player2 : self._generate_initial_view(player2)
        }
        # we move the cursor back up for (num_rows + 3) number of lines
        # +3 consists of the score line, input prompt and the cursor's line
        self._view_reset = RESET_TERMINAL_CODE * (num_rows + 3)


    def initial_views(self):
        """Returns the initial view to be shown to the players"""
        return self._initial_views

    
    def play(self, player, cell_str):
        """Opens the given cell for the given player.

        cell_str is a string of 2 characters, where the first character is 
        the row label and the second character is the column label.

        Return values are dictionaries. There is a key for each player and 
        the value is the view string which must be shown for that player.
        There is also a GAME_OVER_KEY with a boolean value.
        """
        if not cell_str or len(cell_str) != 2:
            return self._invalid_input_response(player)    
        try:
            index = _to_index(self._num_rows, self._num_cols, cell_str[0], cell_str[1])
            play_result = self._game.play(player, index)
        except (IndexError, ValueError) as e:
            return self._invalid_input_response(player)
        players = self._game.players()
        if not play_result.get(WINNER_KEY):
            return {
                players[0] : self._generate_game_view(play_result, players[0]),
                players[1] : self._generate_game_view(play_result, players[1]), 
                GAME_OVER_KEY : False
            }
        else:
            winner = play_result[WINNER_KEY]
            if winner != TIE:
                message = f"%s: %d, %s: %d\nGame over... %s won!\n" % (players[0], play_result[players[0]], players[1], play_result[players[1]], winner)
            else:
                message = f"%s: %d, %s: %d\nGame over... It is a tie!\n" % (players[0], play_result[players[0]], players[1], play_result[players[1]])
                
            return { players[0]: message, players[1]: message, GAME_OVER_KEY : True }


    def _invalid_input_response(self, player):
        if player == self._game.whose_turn():
            return { player : RESET_TERMINAL_CODE + _INPUT_PROMPT, GAME_OVER_KEY : False }
        else:
            return { player : (RESET_TERMINAL_CODE * 2) + _WAIT_MESSAGE + "\n", GAME_OVER_KEY : False }


    def _generate_initial_view(self, player):
        buffer = []
        buffer.append('  ')
        for col_label in _COL_LABELS[0:self._num_cols]:
            buffer.append(col_label)
            buffer.append(' ')
        
        for row_label in _ROW_LABELS[0:self._num_rows]:
            buffer.append('\n')
            buffer.append(row_label)
            buffer.append(' ')
            for i in range(0, self._num_cols):
                buffer.append(CLOSED_CELL_LABEL)
                buffer.append(' ')

        players = self._game.players()
        buffer.append(f"\n%s: 0, %s: 0" % (players[0], players[1]))

        turn = self._game.whose_turn()
        if player == turn:
            buffer.append("\n" + _RESET_LINE_CODE + _INPUT_PROMPT)
        else:
            buffer.append("\n" + _RESET_LINE_CODE + _WAIT_MESSAGE + "\n" + _RESET_LINE_CODE)

        return "".join(buffer)


    def _generate_game_view(self, play_result, player):
        deck = play_result[DECK_KEY]
        buffer = []
        buffer.append(self._view_reset)
        buffer.append('  ')
        for col_label in _COL_LABELS[0:self._num_cols]:
            buffer.append(col_label)
            buffer.append(' ')
        
        for row in range(0, self._num_rows):
            buffer.append('\n')
            buffer.append(_ROW_LABELS[row])
            buffer.append(' ')
            for col in range(0, self._num_cols):
                buffer.append(deck[self._num_cols * row + col])
                buffer.append(' ')

        players = self._game.players()
        buffer.append(f"\n%s: %d, %s: %d" % (players[0], play_result[players[0]], players[1], play_result[players[1]]))

        if player == play_result[WHOSE_TURN_KEY]:
            buffer.append("\n" + _RESET_LINE_CODE + _INPUT_PROMPT)
        else:
            buffer.append("\n" + _RESET_LINE_CODE + _WAIT_MESSAGE + "\n" + _RESET_LINE_CODE)

        return "".join(buffer)
