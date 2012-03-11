# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, generators, print_function, with_statement

import collections
import json

LevelDescriptor = collections.namedtuple('LevelDescriptor', 'version rects')

LevelRect = collections.namedtuple('LevelRect', 'x y w h dx dy')

class LevelFormatError(Exception):
    def __init__(self, message):
        super(LevelFormatError, self).__init__(message)

class LevelEncoder(json.JSONEncoder):
    '''Encodes level descriptor objects to strings'''


    def encode(self, o):
        obj = self.default(o)
        return json.JSONEncoder.encode(self, obj)


    def default(self, o):
        if isinstance(o, LevelDescriptor):
            return {'__class__': 'LevelDescriptor',
                    'version': o.version,
                    'rects': list(self.default(rect) for rect in o.rects)}
        elif isinstance(o, LevelRect):
            d = dict((name, getattr(o, name))
                     for name in 'x y w h dx dy'.split())
            d['__class__'] = 'LevelRect'
            return d
        else:
            return json.JSONEncoder.default(self, o)

class LevelDecoder(json.JSONDecoder):
    '''Decodes level descriptor objects from strings'''
    def __init__(self):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook)

    def object_hook(self, o):
        try:
            cls = o['__class__']
        except KeyError:
            raise LevelFormatError('Cannot understand data: {0:s}'.format(o))
        else:
            if cls == 'LevelDescriptor':
                version = o['version']
                if version != 2:
                    raise LevelFormatError('Can only understand version 2, not {0}'.format(version))
                return LevelDescriptor(version=version, rects=o['rects'])
            elif cls == 'LevelRect':
                del o['__class__']
                return LevelRect(**o)

def dump(level, fp):
    '''serialises a level to an open file-like object'''
    enc = LevelEncoder()
    fp.write(enc.encode(level))

def load(fp):
    '''deserialises a level from an open file-like object'''
    dec = LevelDecoder()
    return dec.decode(fp.read())