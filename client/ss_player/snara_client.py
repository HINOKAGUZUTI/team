from __future__ import annotations
import asyncio
import websockets

from .Board import Board
from .Player import Player
from .Position import Position
from .Block import Block
from .BlockType import BlockType
from .BlockRotation import BlockRotation
import random
import numpy as np


class PlayerClient:
    def __init__(self, player_number: int, socket: websockets.WebSocketClientProtocol, loop: asyncio.AbstractEventLoop):
        self._loop = loop
        self._socket = socket
        self._player_number = player_number
        self.p1turn = 0
        self.p2turn = 0
        self._board = Board()
        self._player = Player(player_number, "pl", "player", None)
        self._opponent = Player(3 - player_number, "op", "opponent", None)

    @property
    def player_number(self) -> int:
        return self._player_number

    async def close(self):
        await self._socket.close()

    async def play(self):
        while True:
            board = await self._socket.recv()
            action = self.create_action(board)
            await self._socket.send(action)
            if action == 'X000':
                raise SystemExit

    def create_action(self, board):
        actions: list[str]
        turn: int

        self._board = Board.from_print_string(board)
        if self.player_number == 1:
            # self.p1Actions = ['U034', 'B037', 'J266', 'M149', 'O763', 'R0A3', 'F0C6', 'K113', 'T021', 'L5D2', 'G251', 'E291', 'D057', 'A053']
            # actions = self.p1Actions
            turn = self.p1turn
            self.p1turn += 1
            # if len(actions) > turn:
            #     return actions[turn]
        else:
            # self.p2Actions = ['A0AA', 'B098', 'N0A5', 'L659', 'K33B', 'J027', 'E2B9', 'C267', 'U07C', 'M3AD', 'O2BB', 'R41C']
            # actions = self.p2Actions
            turn = self.p2turn
            self.p2turn += 1

        # for shape in [b for b in self._player.usable_blocks()[::-1] if b != BlockType.X]:
        for shape in random.sample([b for b in self._player.usable_blocks() if b != BlockType.X], len(self._player.usable_blocks())-1):
            for rot in range(8):
                for y in range(1, self._board.shape_y - np.size(shape.block_map, axis=0)):
                    for x in range(1, self._board.shape_x - np.size(shape.block_map, axis=1)):
                        try:
                            block = Block(shape, BlockRotation(rot))
                            piece = Board.PaddedBlock(self._board, block, Position(x, y))
                            if (self._board.can_place_first_block(self._player, piece) if turn == 0
                                    else self._board.can_place(self._player, piece)):
                                self._player.use_block(block)
                                self._board.place_block(self._player, piece)
                                to_s = "0123456789ABCDE"
                                data = f"{shape.name}{rot}{to_s[x]}{to_s[y]}"
                                print(data)
                                return data

                        except Exception as e:
                            print(type(e), e)
        else:
            # パスを選択
            print("X000")
            return 'X000'

    @staticmethod
    async def create(url: str, loop: asyncio.AbstractEventLoop) -> PlayerClient:
        socket = await websockets.connect(url)
        print('PlayerClient: connected')
        player_number = await socket.recv()
        print(f'player_number: {player_number}')
        return PlayerClient(int(player_number), socket, loop)
