# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, generators, print_function, with_statement

import ctypes
from ctypes import c_char, c_int, c_uint, byref, POINTER
import numpy
import pyglet.gl
from pyglet import gl

__all__ = ['vertex_shader', 'fragment_shader']

class ShaderCompileError(Error):
    pass

c_charp = POINTER(c_char)

def vertex_shader(src):
    '''Returns the id of a new compiled vertex shader'''
    return None

def fragment_shader(src):
    '''Returns the id of a new compiled fragment shader'''
    return None

def shader(shader_type, src):
    assert(shader_type == gl.GL_VERTEX_SHADER or shader_type == gl.GL_FRAGMENT_SHADER)
    s = gl.glCreateShader(shader_type);
    srclen = c_int(len(src))
    psrc = c_charp(src)
    gl.glShaderSource(s, 1, byref(psrc), byref(srclen))
    gl.glCompileShader(s)
    compile_ok = c_int(0)
    gl.glGetShaderiv(s, gl.GL_COMPILE_STATUS, byref(compile_ok))
    if not compile_ok:
        errlen = c_int(0)
        gl.glGetShaderiv(s, gl.GL_INFO_LOG_LENGTH, byref(errlen))
        if errlen <= 0:
            raise ShaderCompileError('unknown error');
        log = c_char
    else:
        return s

