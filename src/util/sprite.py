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
from .atlas import Atlas
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


# the list of active atlases
atlases = list()

# cache of sprites
sprite_cache = dict()

# cache of frames
frame_cache = dict()


class SpriteAtlas(Atlas):
    '''
    A class extending the Atlas class with a texture id.
    '''

    def __init__(self, w, h):
        '''See documentation for Atlas class'''
        super(SpriteAtlas, self).__init__(w, h)
        self.texid = empty_texture((w, h))


class Sprite(object):
    '''
    A combination of a sprite base and associated texture coordinates.
    This class allows sharing of sprite data between different transformed states of a sprite.

    Useful properties:
    sprite.xyuv - packed (4, 4) array of 4 points (x, y, u, v)
        x, y - image corner
        u, v - tex coords for that corner.
    sprite.texid - texture id of this sprite's texture

    sprite.atlas - image atlas for this sprite
    '''

    def __init__(self, atlas, xyuv):
        '''Create a new sprite describing a portion inside an image atlas.
        atlas - the atlas to use.
        xyuv - a float numpy array of shape (4, 4) containing 4 points,
        each being 4 packed floats x, y, u, v where x, y are the coordinates of the sprite rectangle and should
        be [(0, 0), (0, w), (h, w), (h, 0)] (w, h - width, height of the sprite image in pixels)
        and u, v are the texture coordinates for that corner'''

        self.xyuv = xyuv
        self.texid = atlas.texid
        self.atlas = atlas


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
        return sprite_cache[name]
    except KeyError:
        sprite_img = pygame.image.load(os.path.join(dir, name) + '.png')
        n_w, n_h = sprite_img.get_size()

        for a in atlases:
            coords = a.add(n_w, n_h)
            if coords:
                break
        else:
            a = SpriteAtlas(max(512, n_w), max(512, n_h))
            coords = a.add(n_w, n_h)
            atlases.append(a)

        if coords is None:
            raise Exception(format('Could NOT fit ({0}, {1}) image in any atlas!?', n_w, n_h))
        else:
            pass
            #print('fit a', (n_w, n_h), 'image into', a, 'at', coords)
        texture_sub_image(a.texid, coords, sprite_img)

        n_cx, n_cy = coords
        f_uv = numpy.array((n_cx, n_cy, n_cx + n_w, n_cy + n_h), dtype=numpy.float32)
        f_uv[0::2] /= a.w
        f_uv[1::2] /= a.h
        f_xy = numpy.array((0, 0, n_w, n_h), dtype=numpy.float32)
        # indices of the coordinates of the corners of the quad in the
        # above arrays
        indices = ((0, 1), (0, 3), (2, 3), (2, 1))
        f_data = numpy.empty((4, 4), dtype=numpy.float32)
        f_data[:, 0:2] = numpy.take(f_xy, indices)
        f_data[:, 2:4] = numpy.take(f_uv, indices)
        sprite = Sprite(a, f_data)
        sprite_cache[name] = sprite

        return sprite


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
    try:
        return frame_cache[flipped_name]
    except KeyError:
        hbp, hba = frame['hbp'], frame['hba']
        hbp = components.hitbox(hbp.point * (-1, 1) + hbp.size * (-1, 0), hbp.size)
        hba = components.hitbox(hba.point * (-1, 1) + hba.size * (-1, 0), hba.size)
        sprite = frame['sprite']
        f_data = numpy.copy(sprite.xyuv)
        f_data[:, 2:4] = sprite.xyuv[::-1, 2:4]
        newframe={'sprite': Sprite(sprite.atlas, f_data),
                  'sp': frame['sp'] * (-1, 1) + (-sprite.xyuv[2, 0], 0),
                  'hbp': hbp,
                  'hba': hba,
                  'name': flipped_name}
        frame_cache[flipped_name] = newframe
        return newframe


def empty_texture(size, internalformat=gl.GL_RGBA8):
    zeros = numpy.zeros(size, dtype=numpy.uint32).reshape((-1,))
    zeros[0::2] = 0xFFFFFFFF
    zeros[1::2] = 0xFF000000
    _type = gl.GL_UNSIGNED_BYTE
    _format = gl.GL_RGBA
    return texture_from_data(internalformat, size, _format, _type, zeros.ctypes.data)


def format_type_array_from_image(image):
    '''Returns a tuple (format, type, array) characterising the image data.
    depending on bits per pixel:
    format is gl.GL_LUMINANCE/LUMINANCE_ALPHA/RGB/RGBA
    type is gl.GL_UNSIGNED_INT_8_8_8_8_REV for RGBA and gl.GL_UNSIGNED_BYTE otherwise'''

    sig = image.get_bitsize()
    if sig == 8:
        _format = gl.GL_LUMINANCE
        _type = gl.GL_UNSIGNED_BYTE
    elif sig == 16:
        _format = gl.GL_LUMINANCE_ALPHA
        _type = gl.GL_UNSIGNED_BYTE
    elif sig == 24:
        _format = gl.GL_RGB
        _type = gl.GL_UNSIGNED_BYTE
    elif sig == 32:
        _format = gl.GL_RGBA
        _type = gl.GL_UNSIGNED_INT_8_8_8_8_REV
    else:
        raise ValueError('Cannot understand image with bpp', sig)

    if sig == 24:
        _array = pygame.surfarray.pixels3d(image)
    else:
        _array = pygame.surfarray.pixels2d(image)

    return (_format, _type, _array)

def texture_from_image(image, internalformat=None, dimensions=2):
    '''Create and return a new texture id and initialize its data with the given image.
    image - a pygame Surface.
    internalformat - the texture's internal format; if None (the default) will be set to an appropriate one.'''

    format, type, pixels = format_type_array_from_image(image)
    if internalformat is None:
        internalformat = format

    size = [image.get_width(), image.get_height(), 0][:dimensions]
    return texture_from_data(internalformat, size, format, type, pixels.ctypes.data)


def texture_sub_image(texid, place, image, dimensions=2):
    '''Specify a sub-part of a texture with an image.
    place - tuple of coords - the point within the texture of the image's lower-left (see OpenGL) coords'''

    format, type, pixels = format_type_array_from_image(image)

    size = [image.get_width(), image.get_height(), 0][:dimensions]
    texture_sub_data(texid, place, size, format, type, pixels.ctypes.data)


def texture_from_data(internalformat, size, data_format, data_type, data):
    '''Create texture from a data buffer (whatever can be passed as pointer to ctypes)
    internalformat - GL_RGBA8 or GL_RGB8 recommended
    size - a 1-, 2- or 3-tuple describing the image sizes
    data_format - see 'format' parameter of glDrawPixels
    data_type - see 'type' parameter of glDrawPixels
    data - pointer to memory'''

    size = list(size)
    dimensions = len(size)
    binding = getattr(gl, 'GL_TEXTURE_BINDING_{0:d}D'.format(dimensions))
    target = getattr(gl,'GL_TEXTURE_{0:d}D'.format(dimensions))
    texImage = getattr(gl,'glTexImage{0:d}D'.format(dimensions))
    oldbind = ctypes.c_uint(0)
    gl.glGetIntegerv(binding, ctypes.cast(ctypes.byref(oldbind), ctypes.POINTER(ctypes.c_int)))
    texid = ctypes.c_uint(0)
    gl.glEnable(target)
    gl.glGenTextures(1, ctypes.byref(texid))
    gl.glBindTexture(target, texid)
    gl.glTexParameteri(target, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(target, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

    args = [target, 0, internalformat] + size + [0, data_format, data_type, data]

    texImage(*args)
    gl.glBindTexture(target, oldbind)
    return texid


def texture_sub_data(texid, place, size, data_format, data_type, data):
    '''Upload data to part of a texture
    texid - texture id
    place - point within the texture (tuple), coordinates of the lower-left image corner (as per OpenGL)
    See the documentation for texture_from_data for the other args'''

    dimensions = len(size)
    size = list(size)
    place = list(place)
    binding = getattr(gl, 'GL_TEXTURE_BINDING_{0:d}D'.format(dimensions))
    target = getattr(gl,'GL_TEXTURE_{0:d}D'.format(dimensions))
    texSubImage = getattr(gl,'glTexSubImage{0:d}D'.format(dimensions))
    oldbind = ctypes.c_uint(0)
    gl.glEnable(target)
    gl.glGetIntegerv(binding, ctypes.cast(ctypes.byref(oldbind), ctypes.POINTER(ctypes.c_int)))
    gl.glBindTexture(target, texid)

    args = [target, 0] + place + size + [data_format, data_type, data]

    texSubImage(*args)
    gl.glBindTexture(target, oldbind)
