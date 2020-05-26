#!/usr/bin/env python3.7

"""Simple text-based TCP server for the match letters game. Users can play
the game with a telnet client.

# Dependencies:

- curio

Contribute: https://github.com/metanet/match-letters-game

# Init:
virtualenv -p python3 env
source env/bin/activate
pip -r requirements.txt

# Run:
python3 game.server.py [-h] [--host [HOST]] [--port [PORT]] [--rows [ROWS]]
                       [--cols [COLS]]

Optional arguments:
  -h, --help     show this help message and exit
  --host [HOST]  hostname to bind
  --port [PORT]  port to bind
  --rows [ROWS]  number of rows in the game deck
  --cols [COLS]  number of cols in the game deck

# How to play:
You can connect to the game server with a telnet client. For instance, if
the game server is started on localhost:10670, you can connect to it with:
telnet localhost 10670. The game server supports arbitrary number of players.
Since the game is for 2 players, the game server pairs connecting players
in the FIFO order. When a player joins the server, she will wait in the lobby
until another player chimes in. When a player disconnects during the game, the
other player returns back to the lobby. If you want to disconnect your telnet
client, you can hit "CTRL+]", then type "close".
"""

import logging
import string
import argparse
import curio
import game_controller


class _Player:
    def __init__(self, player_name, client, client_stream):
        self.name = player_name
        self.client = client
        self.stream = client_stream
        self.queue = curio.Queue()
        self.active = True

    async def enqueue_message(self, message):
        await self.queue.put(message)

    async def dequeue_message(self):
        message = await self.queue.get()
        return message

    async def write_message(self, message):
        await _do_write_message(self.stream, message)

    def set_inactive(self):
        self.active = False

    def is_active(self):
        return self.active


class _Randezvous:
    def __init__(self):
        self.player1 = None
        self.player2 = None
        self.game_queue = curio.Queue()
        self.task_group = curio.TaskGroup(wait=any)

    def add_player(self, player):
        if not self.player1:
            self.player1 = player
        elif not self.player2:
            self.player2 = player
        else:
            return False
        return True

    def is_full(self):
        return self.player1 and self.player2

    def get_player(self, player_name):
        if not self.player1 or not self.player2:
            raise ValueError
        return self.player1 if self.player1 == player_name else self.player2

    def get_opponent(self, player):
        if not self.player1 or not self.player2:
            raise KeyError
        return self.player1 if self.player2 == player else self.player2

    def reset(self):
        self.player1 = None
        self.player2 = None
        self.reset_game()

    def reset_game(self):
        self.game_queue = curio.Queue()
        self.task_group = curio.TaskGroup(wait=any)


class _Lobby:
    def __init__(self):
        self.randezvous = _Randezvous()


_DEFAULT_HOST = "localhost"
_DEFAULT_PORT = 10670
_DEFAULT_NUM_ROWS = 4
_DEFAULT_NUM_COLS = 6


_lobby = _Lobby()
_START_GAME = -1
_NUM_ROWS = _DEFAULT_NUM_ROWS
_NUM_COLS = _DEFAULT_NUM_COLS


async def _do_write_message(client_stream, message):
    await client_stream.write((message).encode("UTF-8"))


def _decode_message(message):
    return message.strip().decode("UTF-8")


async def _player_outbound(player):
    while True:
        message = await player.dequeue_message()
        await player.write_message(message)


async def _player_inbound(player, game_queue):
    async for message in player.stream:
        try:
            decoded = _decode_message(message)
            await game_queue.put((player, decoded))
        except Exception as e:
            logging.getLogger(player.name).error(
                "decoding of %s's message: %d failed with: %s", player.name, message, e)
            break
    player.set_inactive()


async def _play_game(randezvous):
    logger = logging.getLogger("game")
    game = None

    while True:
        message = await randezvous.game_queue.get()
        if message == _START_GAME:
            logger.info(f"Starting the game between %s and %s!" %
                        (randezvous.player1.name, randezvous.player2.name))
            game = game_controller.GameController(
                _NUM_ROWS, _NUM_COLS, randezvous.player1.name, randezvous.player2.name)
            views = game.initial_views()

            await randezvous.player1.enqueue_message(views[randezvous.player1.name])
            await randezvous.player2.enqueue_message(views[randezvous.player2.name])
            continue

        (player, move) = message
        if not game:
            await player.enqueue_message("The game has not started yet. Still waiting for the second player...\n")
            continue

        logger.info("handling \"%s\" from %s", move, player.name)

        try:
            views = game.play(player.name, move)
            if views.get(randezvous.player1.name):
                await randezvous.player1.enqueue_message(views[randezvous.player1.name])
            if views.get(randezvous.player2.name):
                await randezvous.player2.enqueue_message(views[randezvous.player2.name])
            if views[game_controller.GAME_OVER_KEY]:
                randezvous.reset_game()
                return
        except Exception as e:
            logger.error("%s's %s failed with: %s", player.name, move, e)


async def _get_player_name(client_stream):
    while True:
        await _do_write_message(client_stream, "Your name: ")
        player_name = _decode_message(await client_stream.readline())
        if player_name:
            return player_name
        else:
            await _do_write_message(client_stream, game_controller.RESET_TERMINAL_CODE)


async def _start_player_io(randezvous, player):
    await randezvous.task_group.spawn(_player_outbound, player)
    await randezvous.task_group.spawn(_player_inbound, player, randezvous.game_queue)


async def _start_game(randezvous, player, is_first_game):
    opponent = randezvous.get_opponent(player)
    if is_first_game:
        # players will play against each other for the first time
        await player.enqueue_message(f"You will play with %s.\n" % (opponent.name))
        await opponent.enqueue_message(f"You will play with %s.\n" % (player.name))
        await randezvous.game_queue.put(_START_GAME)
        async with randezvous.task_group:
            await _start_player_io(randezvous, player)
    else:
        # players will play another game togerher
        await player.enqueue_message(f"Starting a new game with %s.\n" % (opponent.name))
        async with randezvous.task_group:
            await _start_player_io(randezvous, player)
            if player == randezvous.player2:
                # make sure only one player starts the game loop
                await randezvous.game_queue.put(_START_GAME)
                await randezvous.task_group.spawn(_play_game, randezvous)


async def _join_lobby(player, client_stream):
    logger = logging.getLogger("lobby")

    add_this_player = True
    while True:
        if add_this_player:
            # I might be adding myself into my previous randevous or a totally new one
            my_randezvous = _lobby.randezvous
            my_randezvous.add_player(player)

        if my_randezvous.is_full():
            if _lobby.randezvous == my_randezvous:
                # this randezvous is done. create a new one for newcomers
                _lobby.randezvous = _Randezvous()

            await _start_game(my_randezvous, player, add_this_player)
        else:
            await player.enqueue_message("Waiting for the second player...\n")
            async with my_randezvous.task_group:
                await _start_player_io(my_randezvous, player)
                await my_randezvous.task_group.spawn(_play_game, my_randezvous)

        # either the game is normally completed or at least one player has left...
        if player.is_active():
            # there are definitely two players in the randezvous
            opponent = my_randezvous.get_opponent(player)
            if opponent.is_active():
                # game over. continue with the same randevous since both players are here
                logger.info(f"%s and %s are starting a new game..." %
                            (player.name, opponent.name))
                add_this_player = False
            else:
                logger.warning(f"%s has left. %s will wait for a new opponent..." % (
                    opponent.name, player.name))
                await player.enqueue_message(f"\n%s has left.\n" % (opponent.name))
                add_this_player = True
                # I might add myself into the same randevous so resetting it
                my_randezvous.reset()
        else:
            if not my_randezvous.is_full():
                # if I am the only player in the current randezvous, reset it
                # so that new players can use it.
                my_randezvous.reset()
            break

    logger.info("%s has left...", player.name)


async def _client_handler(client, addr):
    logger = logging.getLogger("client_handler")
    logger.info("%s connected.", addr)

    try:
        async with client:
            client_stream = client.as_stream()
            player_name = await _get_player_name(client_stream)
            logger.info("%s's name is %s", addr, player_name)
            await _do_write_message(client_stream, f"Welcome %s!\n" % (player_name))
            await _join_lobby(_Player(player_name, client, client_stream), client_stream)

        logger.info("%s closed.", addr)
    except Exception as e:
        logger.error("%s failed with: %s.", addr, e)


async def start_game_server(host, port):
    """Starts the match symbols game TCP server on the given host:port"""
    async with curio.TaskGroup() as g:
        await g.spawn(curio.tcp_server, host, port, _client_handler)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Starts a TPC game server for the match symbols game.')
    parser.add_argument("--host", dest="host", nargs='?', default=_DEFAULT_HOST,
                        help="hostname to bind")
    parser.add_argument("--port", dest="port", type=int, nargs='?', default=_DEFAULT_PORT,
                        help="port to bind")
    parser.add_argument('--rows', dest="rows", type=int, nargs='?', default=_DEFAULT_NUM_ROWS,
                        help='number of rows in the game deck')
    parser.add_argument('--cols', dest="cols", type=int, nargs='?', default=_DEFAULT_NUM_COLS,
                        help='number of cols in the game deck')

    args = parser.parse_args()
    if args.rows:
        _NUM_ROWS = args.rows
    if args.cols:
        _NUM_COLS = args.cols

    print(f"Starting the TCP server on %s:%d for the game deck of %dx%d." %
          (args.host, args.port, args.rows, args.cols))

    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(name)s : %(message)s', level=logging.INFO)
    curio.run(start_game_server(args.host, args.port))
