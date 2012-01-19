# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, generators, print_function, with_statement

import ctypes
from ctypes import c_char, c_char_p, c_int, c_uint, byref, POINTER, pointer
import numpy
import pyglet.gl
from pyglet import gl


__all__ = ['vertex_shader', 'fragment_shader', 'program']


LP_c_char = POINTER(c_char)


class ShaderCompileError(Exception):
    pass


class ProgramLinkError(Exception):
    pass


def vertex_shader(src):
    '''Returns the id of a new compiled vertex shader'''
    return shader(gl.GL_VERTEX_SHADER, src)


def fragment_shader(src):
    '''Returns the id of a new compiled fragment shader'''
    return shader(gl.GL_FRAGMENT_SHADER, src)


def shader(shader_type, src):
    assert(shader_type == gl.GL_VERTEX_SHADER or shader_type == gl.GL_FRAGMENT_SHADER)
    s = gl.glCreateShader(shader_type);
    srclen = c_int(len(src))
    psrc = c_char_p(src)
    lpsrc = ctypes.cast(psrc, LP_c_char)
    gl.glShaderSource(s, 1, pointer(lpsrc), byref(srclen))
    gl.glCompileShader(s)
    return check_shader_or_program_status(s)


def program(*shaders):
    p = gl.glCreateProgram()
    for s in shaders:
        gl.glAttachShader(p, s)
    gl.glLinkProgram(p)
    return check_shader_or_program_status(p)


def check_shader_or_program_status(obj):
    '''checks if the given shader or program object has been compiled or linked successfully.
    Raises an exception if not and deletes the object.
    Returns the object otherwise'''

    if gl.glIsShader(obj):
        getiv = gl.glGetShaderiv
        getlog = gl.glGetShaderInfoLog
        statusflag = gl.GL_COMPILE_STATUS
        delete = gl.glDeleteShader
        ErrorClass = ShaderCompileError
    elif gl.glIsProgram(obj):
        getiv = gl.glGetProgramiv
        getlog = gl.glGetProgramInfoLog
        statusflag = gl.GL_LINK_STATUS
        delete = gl.glDeleteProgram
        ErrorClass = ProgramLinkError
    else:
        raise ValueError('object {} neither shader nor prorgam'.format(obj))

    ok = c_int(0)
    getiv(obj, statusflag, byref(ok))
    if not ok:
        errlen = c_int(0)
        getiv(obj, gl.GL_INFO_LOG_LENGTH, byref(errlen))
        errlen = errlen.value
        if errlen <= 0:
            error = 'unknown error'
        else:
            log = ctypes.create_string_buffer('', errlen)
            getlog(obj, errlen, None, log)
            error = log.value
        delete(obj)
        raise ErrorClass(error)
    else:
        return obj



