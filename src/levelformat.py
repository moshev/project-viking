import collections

LevelDescriptor = collections.namedtuple('LevelDescriptor', 'version rects')

LevelRect = collections.namedtuple('LevelRect', 'x y w h dx dy')

class LevelFormatError(Exception):
    def __init__(self, message):
        super(LevelFormatError, self).__init__(message)

