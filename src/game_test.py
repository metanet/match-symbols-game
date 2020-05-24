
import pytest
from game import Game, CLOSED_CELL_LABEL, OPEN_CELL_LABEL, WINNER_KEY, WHOSE_TURN_KEY, DECK_KEY
from string import ascii_lowercase



_symbols = ascii_lowercase[:5]
_player1 = "p1"
_player2 = "p2"


@pytest.fixture
def game():
    return Game(_symbols, _player1, _player2)


def test_game_init(game):
    assert game.whose_turn() == _player1 or game.whose_turn() == _player2


def test_first_play(game):
    player = game.whose_turn()

    result = game.play(player, 0)

    assert game.whose_turn() == player
    assert result[WHOSE_TURN_KEY] == player
    assert result[DECK_KEY][0] in _symbols
    assert result[_player1] == 0
    assert result[_player2] == 0
    for symbol in result[DECK_KEY][1:]:
        assert symbol == CLOSED_CELL_LABEL


def test_failed_second_play(game):
    player = game.whose_turn()
    all_letters = game.peek()

    game.play(player, all_letters[0][0])
    result2 = game.play(player, all_letters[1][0])

    assert result2[DECK_KEY][all_letters[0][0]] == CLOSED_CELL_LABEL
    assert result2[DECK_KEY][all_letters[1][0]] in _symbols
    assert result2[_player1] == 0
    assert result2[_player2] == 0
    assert result2[WHOSE_TURN_KEY] and result2[WHOSE_TURN_KEY] != player


def test_new_play_after_fail(game):
    player = game.whose_turn()
    all_letters = game.peek()

    game.play(player, all_letters[0][0])
    game.play(player, all_letters[1][0])
    player = game.whose_turn()

    result = game.play(player, 0)

    assert game.whose_turn() == player
    assert result[WHOSE_TURN_KEY] == player
    assert result[_player1] == 0
    assert result[_player2] == 0
    assert result[DECK_KEY][0] in _symbols
    for symbol in result[DECK_KEY][1:]:
        assert symbol == CLOSED_CELL_LABEL


def test_successful_second_play(game):
    player = game.whose_turn()
    other_player = _player1 if player == _player2 else _player2
    all_letters = game.peek()
    indices = all_letters[0]

    game.play(player, indices[0])
    result2 = game.play(player, indices[1])

    assert result2[DECK_KEY][indices[0]] == OPEN_CELL_LABEL
    assert result2[DECK_KEY][indices[1]] == OPEN_CELL_LABEL
    assert result2[WHOSE_TURN_KEY] == player
    assert result2[player] == 1
    assert result2[other_player] == 0


def test_new_play_after_open(game):
    player = game.whose_turn()
    other_player = _player1 if player == _player2 else _player2
    all_indices = game.peek()

    game.play(player, all_indices[0][0])
    game.play(player, all_indices[0][1])

    result = game.play(player, all_indices[1][0])

    assert result[DECK_KEY][all_indices[0][0]] == OPEN_CELL_LABEL
    assert result[DECK_KEY][all_indices[0][1]] == OPEN_CELL_LABEL
    assert result[DECK_KEY][all_indices[1][0]] != OPEN_CELL_LABEL
    assert result[WHOSE_TURN_KEY] == player
    assert result[player] == 1
    assert result[other_player] == 0


def test_win(game):
    player = game.whose_turn()
    other_player = _player1 if player == _player2 else _player2
    all_letters = game.peek()
    win_score = len(all_letters) // 2 + 1
    for indices in all_letters[0:win_score]:
        result = game.play(player, indices[0])
        result = game.play(player, indices[1])

    assert result[WINNER_KEY] == player
    assert result[player] == win_score
    assert result[other_player] == 0


def test_play_by_invalid_player(game):
    turn = game.whose_turn()
    other_player = _player1 if turn == _player2 else _player2

    with pytest.raises(ValueError):
        game.play(other_player, 0)


def test_play_negative_index(game):
    turn = game.whose_turn()
    with pytest.raises(IndexError):
        game.play(turn, -1)


def test_play_overflowing_index(game):
    turn = game.whose_turn()
    with pytest.raises(IndexError):
        game.play(turn, len(_symbols) * 2)


def test_play_turned_index(game):
    turn = game.whose_turn()

    game.play(turn, 0)
    with pytest.raises(ValueError):
        game.play(turn, 0)


def test_play_open_index(game):
    turn = game.whose_turn()
    all_letters = game.peek()

    game.play(turn, all_letters[0][0])
    game.play(turn, all_letters[0][1])

    with pytest.raises(ValueError):
        game.play(turn, all_letters[0][0])


def test_init_game_with_duplicate_symbols():
    with pytest.raises(ValueError):
        game = Game("aabcdef", _player1, _player2)


def test_missing_first_player():
    with pytest.raises(ValueError):
        game = Game("abcd", None, _player2)


def test_missing_second_player():
    with pytest.raises(ValueError):
        game = Game("abcd", _player1, None)


def test_duplicate_players():
    with pytest.raises(ValueError):
        game = Game("abcd", _player1, _player1)