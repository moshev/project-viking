# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, generators, print_function, with_statement


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


__all__ = [
    'Sprite',
    'load_texture',
    'load_sprite',
    'load_frame',
    'load_frame_sequence',
    'flip_frame',
    'texture_from_image',
    ]


# so we don't load images twice, store mapping of loaded sprite to file in here
spritecommondata_cache = dict()

# cache of frames
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
            self._texid = texture_from_image(self.image)

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


def load_texture(filename, dimensions=2):
    ''' Loads a texture and returns its id.
    filename - file to open
    dimensions - how many dimensions the texture has. 1, 2 or 3. '''
    tex_img = pygame.image.load(filename)
    return texture_from_image(tex_img, dimensions=dimensions)


def load_sprite(dir, name):
    '''
    Loads a sprite object with an image set to dir/name
    '''
    try:
        return Sprite(spritecommondata_cache[name])
    except KeyError:
        sprite_img = pygame.image.load(os.path.join(dir, name) + '.png')
        commondata = SpriteCommonData(sprite_img)
        spritecommondata_cache[name] = commondata
        return Sprite(commondata)


def load_frame(dir, name):
    '''
    Returns a dict
    'sprite': loaded image
    'sp': sprite point
    'hbp': passive hitbox
    'hba': active hitbox
    '''
    try:
        return frame_cache[name]
    except KeyError:
        sprite = load_sprite(dir, name)
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
    texcoords = frame['sprite'].texcoords[::-1]
    newframe={'sprite': Sprite(frame['sprite'].data, texcoords),
              'sp': frame['sp'] * (-1, 1) + (-frame['sprite'].quad[2, 0], 0),
              'hbp': hbp,
              'hba': hba,
              'name': flipped_name}
    frame_cache[flipped_name] = newframe
    return newframe

def texture_from_image(image, internalformat=None, dimensions=2):
    '''Create and return a new texture id and initialize its data with the given image.
    image - a pygame Surface.
    internalformat - the texture's internal format; if None (the default) will be set to an appropriate one.'''

    sig = image.get_shifts()
    if sig == (0, 8, 16, 0):
        _format = gl.GL_RGB
        _type = gl.GL_UNSIGNED_BYTE
        if internalformat is None:
            internalformat = gl.GL_RGB8
    elif sig == (0, 8, 16, 24):
        _format = gl.GL_RGBA
        _type = gl.GL_UNSIGNED_INT_8_8_8_8_REV
        if internalformat is None:
            internalformat = gl.GL_RGBA8
    else:
        return None

    binding = gl.__dict__['GL_TEXTURE_BINDING_{:d}D'.format(dimensions)]
    target = gl.__dict__['GL_TEXTURE_{:d}D'.format(dimensions)]
    texImage = gl.__dict__['glTexImage{:d}D'.format(dimensions)]
    oldbind = ctypes.c_uint(0)
    gl.glGetIntegerv(binding, ctypes.cast(ctypes.byref(oldbind), ctypes.POINTER(ctypes.c_int)))
    texid = ctypes.c_uint(0)
    gl.glEnable(target)
    gl.glGenTextures(1, ctypes.byref(texid))
    gl.glBindTexture(target, texid)
    gl.glTexParameteri(target, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
    gl.glTexParameteri(target, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)

    if image.get_bytesize() == 3:
        pixels = pygame.surfarray.pixels3d(image)
    else:
        pixels = pygame.surfarray.pixels2d(image)

    imagesize = [image.get_width(), image.get_height(), 0][:dimensions]
    args = [target, 0, internalformat] + imagesize + [0, _format, _type, pixels.ctypes.data]

    texImage(*args)
    gl.glBindTexture(target, oldbind)
    return texid


