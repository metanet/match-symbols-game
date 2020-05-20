# Match Symbols Game with Python Coroutines

This repository contains the source code of a very simple game. I implemented
this game to improve my Python skills and play with coroutine-based programming 
in Python (thank you, covid-19!).

This game is played by 2 people in turns. There is a deck of symbols and 
initially all symbols are closed. Each player opens 2 cells on her turn. If both 
cells have the same symbol, the player's score is incremented and the player 
opens 2 other cells. Otherwise, it becomes the other player's turn. The game is
completed when either one of the players manages to match more than half of the 
symbols, or both match the same number of cells, which is a tie. You can see
the game logic at 
[`game.py`](https://github.com/metanet/match-symbols-game/blob/master/game.py).

The game is played via a simple and text-based TPC server which is available
inside 
[`game_server.py`](https://github.com/metanet/match-symbols-game/blob/master/game_server.py). 
The server is implemented with the 
[curio](https://github.com/dabeaz/curio) library which can be installed with
`pip install curio`. Once you have `curio`, you can start the game server with
`python3 game_server.py`. It starts a TCP server on `localhost:6700` by default.
You can connect to the server with `telnet localhost 6700`. 

The game server supports arbitrary number of players. Since the game is for 2
players, the game server pairs connecting players in the FIFO order. When a
player joins the server, she will wait in the lobby until another player chimes
in. When a player disconnects during the game, the other player returns back to 
the lobby. If you want to disconnect your telnet client, you can hit `CTRL+]`, 
then type `close`.