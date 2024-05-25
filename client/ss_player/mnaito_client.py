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

        best_score = float('-inf')
        best_action = 'X000'
    
        for shape in [b for b in self._player.usable_blocks() if b != BlockType.X]:
            for rot in range(8):
                #if is_valid_rotation(shape.name, rot) == 0 :
                #	continue
                for y in range(1, self._board.shape_y - np.size(shape.block_map, axis=0)):
                    for x in range(1, self._board.shape_x - np.size(shape.block_map, axis=1)):
                        try:
                            block = Block(shape, BlockRotation(rot))
                            piece = Board.PaddedBlock(self._board, block, Position(x, y))
                            if (self._board.can_place_first_block(self._player, piece) if turn == 0
                                    else self._board.can_place(self._player, piece)):
                                self._player.use_block(block)
                                self._board.place_block(self._player, piece)
                            
                                score = self.minmax(self._board, 3, float('-inf'), float('inf'), False)
                            
                                self._player.unuse_block(block)
                                self._board.remove_block(self._player, piece)

                                if score > best_score:
                                    best_score = score
                                    to_s = "0123456789ABCDE"
                                    best_action = f"{shape.name}{rot}{to_s[x]}{to_s[y]}"
                        except ValueError as e:
                            print(f"Invalid Position or Block: {e}")

        print(best_action)
        return best_action

    #def is_valid_rotation(shape, rot) :
    #	if rot == 0 :
    #		return 1 :
    #	if shape == 'A' :
    #		return 0
    #	else if shape == 'B' or shape == 'C' :
    #		if rot == 2
    #			return 1
    #		else :
    #			return 0
    #	

    def evaluate_board(self, board):
        player_score = self.calculate_score(board, self._player)
        opponent_score = self.calculate_score(board, self._opponent)
        return player_score - opponent_score

    #def	calculate_score(self, board, player):
    #    influence_area = 0
    #    for y in range(1, board.shape_y - np.size(shape.block_map, axis=0)):
    #        for x in range(1, board.shape_x - np.size(shape.block_map, axis=1)):
                

    def calculate_score(self, board, player):
    	usable_blocks = player.usable_blocks()
    	placeable_positions = 0
    	for shape in usable_blocks:
        	for rot in range(8):
            	for y in range(1, board.shape_y - np.size(shape.block_map, axis=0)):
                	for x in range(1, board.shape_x - np.size(shape.block_map, axis=1)):
                    	block = Block(shape, BlockRotation(rot))
                    	piece = Board.PaddedBlock(board, block, Position(x, y))
                    	if board.can_place(player, piece):
                        	placeable_positions += 1
    	placed_blocks_area = sum(np.sum(block.block_map) for block in player.used_blocks)
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
