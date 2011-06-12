from __future__ import print_function, absolute_import

import cPickle as pickle
import os
import sys
import numpy
import pygame.image
import pyglet
import components
import ctypes
from itertools import repeat, izip
from pyglet import gl


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


frame_cache = dict()


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
    data['sprite'] = sprite
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
    newframe={'sprite': pygame.transform.flip(frame['sprite'], True, False),
              'sp': frame['sp'] * (-1, 1) + (-frame['sprite'].get_width(), 0),
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
    gl.glFinish()
    gl.glBindTexture(gl.GL_TEXTURE_2D, oldbind)
    return texid

