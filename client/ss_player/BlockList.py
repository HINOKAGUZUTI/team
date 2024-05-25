import numpy as np

from .Block import Block
from .BlockType import BlockType
from .BlockRotation import BlockRotation


class BlockList:
    def __init__(self):
        self.blocklist = {f"{btype}{brot}": Block(btype, brot) for brot in BlockRotation for btype in BlockType if btype != BlockType.X}
