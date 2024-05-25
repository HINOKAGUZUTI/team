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
        self._board = Board.from_print_string(board)

        if self.player_number == 1:
            turn = self.p1turn
            self.p1turn += 1
        else:
            turn = self.p2turn
            self.p2turn += 1

        # 初手の例外処理
        if turn == 0:
            return self.initial_move()

        best_score = float('-inf')
        best_action = 'X000'
        n_searched = 0

        for shape in [b for b in self._player.usable_blocks() if b != BlockType.X]:
            for rot in range(8):
                for y in range(1, self._board.shape_y - shape.block_map.shape[0] + 1):
                    for x in range(1, self._board.shape_x - shape.block_map.shape[1] + 1):
                        try:
                            n_searched += 1
                            block = Block(shape, BlockRotation(rot))
                            piece = Board.PaddedBlock(self._board, block, Position(x, y))
                            if self._player.can_use_block(block) and self._board.can_place(self._player, piece):
                                #print(piece.map)
                                self._player.use_block(block)
                                self._board.place_block(self._player, piece)

                                score = self.minmax(self._board, 0, float('-inf'), float('inf'), False)

                                self._player.unuse_block(block)
                                self._board.remove_block(self._player, piece)

                                if score >= best_score:
                                    best_score = score
                                    to_s = "0123456789ABCDE"
                                    best_action = f"{shape.name}{rot}{to_s[x]}{to_s[y]}"
                                    print(n_searched, ":", best_action)
                                    if n_searched >= 100:
                                        self._player.use_block(block)
                                        self._board.place_block(self._player, piece)
                                        return best_action
                                else:
                                    pass

                        except ValueError as e:
                            print(f"Invalid Position or Block: {e}")

        # self._player.use_block(block)
        # self._board.place_block(self._player, piece)
        print(n_searched, ":", best_action)
        return best_action

#

    def initial_move(self):
        largest_block = max(list(self._player.usable_blocks())[::-1], key=lambda b: np.sum(Block(b, BlockRotation(0)).block_map))
        rotations = [BlockRotation(rot) for rot in range(8)]
        positions = []
        print(self._board.to_print_string())

        if self.player_number == 1:
            target_position = Position(5, 5)
        else:
            target_position = Position(10, 10)

        for rot in rotations:
            block = Block(largest_block, rot)
            for y in range(target_position.y - block.block_map.shape[0] + 2, target_position.y + 2):
                for x in range(target_position.x - block.block_map.shape[1] + 2, target_position.x + 2):
                    try:
                        piece = Board.PaddedBlock(self._board, block, Position(x, y))
                        #print(piece.map)
                        if self._board.can_place_first_block(self._player, piece):
                            to_s = "0123456789ABCDE"
                            data = f"{largest_block.name}{rot.value}{to_s[x]}{to_s[y]}"
                            print(data)
                            self._player.use_block(block)
                            return data
                    except ValueError as e:
                        print(e)
                        pass

        raise ValueError("No valid initial move found")

    def evaluate_board(self, board: Board):
        player_score = self.calculate_score(board, self._player)
        opponent_score = self.calculate_score(board, self._opponent)
        print("eveluate score:", player_score)
        return player_score - opponent_score

    def calculate_score(self, board: Board, player: Player):
        # usable_blocks = player.usable_blocks()
        # placeable_positions = 0
        # for shape in usable_blocks:
        #     for rot in range(8):
        #         for y in range(1, board.shape_y - np.size(shape.block_map, axis=0)):
        #             for x in range(1, board.shape_x - np.size(shape.block_map, axis=1)):
        #                 block = Block(shape, BlockRotation(rot))
        #                 piece = Board.PaddedBlock(board, block, Position(x, y))
        #                 if board.can_place(player, piece):
        #                     placeable_positions += 1

        corners = Board()
        corners.__board = np.copy(board.now_board())
        # Board.PaddedBlock._decorate_corner(corners)
        placeable_positions = np.sum(corners.now_board())
        placed_blocks_area = sum(np.sum(block.block_map) for block in player.used_blocks())
        return placeable_positions + placed_blocks_area

    def minmax(self, board, depth, alpha, beta, is_maximizing_player):
        if depth == 0:
            return self.evaluate_board(board)

        if is_maximizing_player:
            max_eval = float('-inf')
            for shape in self._player.usable_blocks():
                for rot in range(8):
                    for y in range(1, board.shape_y - np.size(shape.block_map, axis=0)):
                        for x in range(1, board.shape_x - np.size(shape.block_map, axis=1)):
                            try:
                                block = Block(shape, BlockRotation(rot))
                                piece = Board.PaddedBlock(board, block, Position(x, y))
                                if board.can_place(self._player, piece):
                                    self._player.use_block(block)
                                    board.place_block(self._player, piece)

                                    eval = self.minmax(board, depth - 1, alpha, beta, False)

                                    self._player.unuse_block(block)
                                    board.remove_block(self._player, piece)

                                    max_eval = max(max_eval, eval)
                                    alpha = max(alpha, eval)
                                    if beta <= alpha:
                                        break
                            except ValueError:
                                continue
            return max_eval
        else:
            min_eval = float('-inf')
            for shape in self._opponent.usable_blocks():
                for rot in range(8):
                    for y in range(1, board.shape_y - np.size(shape.block_map, axis=0)):
                        for x in range(1, board.shape_x - np.size(shape.block_map, axis=1)):
                            try:
                                block = Block(shape, BlockRotation(rot))
                                piece = Board.PaddedBlock(board, block, Position(x, y))
                                if board.can_place(self._opponent, piece):
                                    self._opponent.use_block(block)
                                    board.place_block(self._opponent, piece)

                                    eval = self.minmax(board, depth - 1, alpha, beta, True)

                                    self._opponent.unuse_block(block)
                                    board.remove_block(self._opponent, piece)

                                    min_eval = min(min_eval, eval)
                                    beta = min(beta, eval)
                                    if beta <= alpha:
                                        break
                            except ValueError:
                                continue
            return min_eval

    @staticmethod
    async def create(url: str, loop: asyncio.AbstractEventLoop) -> PlayerClient:
        socket = await websockets.connect(url)
        print('PlayerClient: connected')
        player_number = await socket.recv()
        print(f'player_number: {player_number}')
        return PlayerClient(int(player_number), socket, loop)
