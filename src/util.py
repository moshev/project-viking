from __future__ import print_function, absolute_import

import cPickle as pickle
import os
import sys
import numpy
import pygame.image
import pyglet
import pyglet.gl
import components
import ctypes
from itertools import repeat, izip
from pyglet import gl


# so we don't load images twice, store mapping of loaded sprite to file in here
frame_cache = dict()


class SpriteCommonData(object):
    '''
    A class holding an image that can be loaded to a texture id.

    self.quad - array of 4 * 2 floats, shape=(4, 2) specifying a quad with the size of the given sprite
    '''

    def __init__(self, image):
        '''Create a new sprite from a pygame surface (image)'''
        self.image = image
        k = image.get_size()
        self.quad = numpy.array((0, 0, 0, k[1], k[0], k[1], k[0], 0), dtype=numpy.float32).reshape(4, 2)
        self._texid = None

    @property
    def texid(self):
        if self._texid is None:
            self._texid = texture_from_image(self.image, gl.GL_RGB8)

        return self._texid


class Sprite(object):
    '''
    A combination of a sprite base and associated texture coordinates.
    This class allows sharing of sprite data between different transformed states of a sprite.
    '''

    def __init__(self, data, texcoords=None):
        '''Create a new sprite from a SpriteCommonData object and attach some texture coordinates.
        if texcoords is None, an array of texcoords are generated to draw the sprite normally.'''

        self.data = data
        if texcoords is None:
            self.texcoords = numpy.array((0, 0, 0, 1, 1, 1, 1, 0), dtype=numpy.float32).reshape(4, 2)
        else:
            self.texcoords = texcoords

    @property
    def texid(self):
        '''The texture id corresponding to this sprite'''
        return self.data.texid

    @property
    def quad(self):
        '''This sprite's quad's vertices as an array of floats, shape=(4, 2)'''
        return self.data.quad


def repeat_each(items, repeats):
    '''Iterate items, repeatedly yielding each item the corresponding times.'''
    for i, r in izip(items, repeats):
        for j in repeat(i, r):
            yield j


def arrayify(x):
    '''Constructs a float array from x'''
    return numpy.array(x, dtype=float)


def find_datadir():
    '''
    Returns an absolute path to the 'data' directory.
    Source and data should be laid out like so:
        +/
        |
        +--+ data
        |  | ... files ...
        |
        +--+ src
           | sys.argv[0]
    '''
    return os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), '..', 'data'))


def load_frame(dir, name):
    '''
    Returns a dict
    'sprite': loaded image
    'sp': sprite point
    'hbp': passive hitbox
    'hba': active hitbox
    '''
    if name in frame_cache:
        return frame_cache[name]
    sprite = pygame.image.load(os.path.join(dir, name) + '.png')
    datafile = file(os.path.join(dir, name) + '.points')
    data = pickle.load(datafile)
    datafile.close()
    commondata = SpriteCommonData(sprite)
    data['sprite'] = Sprite(commondata)
    data['name'] = name
    frame_cache[name] = data
    return data


def load_frame_sequence(dir, basename, number, start=1):
    '''
    Loads dir/basenameS.png through dir/basenameN+S.png and returns them as a list.
    S and N are start and number, respectively.
    '''
    return [load_frame(dir, basename + str(n)) for n in range(start, number + start)]


def flip_frame(frame):
    flipped_name = frame['name'] + '/flipped'
    if flipped_name in frame_cache:
        return frame_cache[flipped_name]
    hbp, hba = frame['hbp'], frame['hba']
    hbp = components.hitbox(hbp.point * (-1, 1) + hbp.size * (-1, 0), hbp.size)
    hba = components.hitbox(hba.point * (-1, 1) + hba.size * (-1, 0), hba.size)
    texcoords = frame['sprite'].texcoords.take((2, 3, 0, 1), axis=0)
    newframe={'sprite': Sprite(frame['sprite'].data, texcoords),
              'sp': frame['sp'] * (-1, 1) + (-frame['sprite'].quad[2, 1], 0),
              'hbp': hbp,
              'hba': hba,
              'name': flipped_name}
    frame_cache[flipped_name] = newframe
    return newframe

def texture_from_image(image, internalformat):
    '''Create and return a new texture id and initialize its data with the given image.
    image - a pygame Surface.
    internalformat - the texture's internal format.'''

    sig = image.get_shifts()
    if sig == (0, 8 ,16, 0):
        _format = gl.GL_RGB
        _type = gl.GL_UNSIGNED_BYTE
    elif sig == (0, 8, 16, 24):
        _format = gl.GL_BGRA
        _type = gl.GL_UNSIGNED_INT_8_8_8_8_REV
    else:
        return None

    oldbind = ctypes.c_uint(0)
    gl.glGetIntegerv(gl.GL_TEXTURE_BINDING_2D, ctypes.cast(ctypes.byref(oldbind), ctypes.POINTER(ctypes.c_int)))
    texid = ctypes.c_uint(0)
    gl.glEnable(gl.GL_TEXTURE_2D)
    gl.glGenTextures(1, ctypes.byref(texid))
    gl.glBindTexture(gl.GL_TEXTURE_2D, texid)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)

    if image.get_bytesize() == 3:
        pixels = pygame.surfarray.pixels3d(image)
    else:
        pixels = pygame.surfarray.pixels2d(image)
    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, internalformat, image.get_width(), image.get_height(),
                    0, _format, _type, pixels.ctypes.data)
    gl.glBindTexture(gl.GL_TEXTURE_2D, oldbind)
    return texid

