# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, generators, print_function, with_statement

import ctypes
from ctypes import c_char, c_char_p, c_int, c_uint, byref, POINTER, pointer
import numpy
import pyglet.gl
from pyglet import gl


__all__ = ['GLProgram']


SETTERSF = [gl.glUniform1f, gl.glUniform2f, gl.glUniform3f, gl.glUniform4f]


class GLProgram(object):
    def __init__(self, vertex_shader_src, fragment_shader_src):
        vsid = vertex_shader(vertex_shader_src)
        fsid = fragment_shader(fragment_shader_src)
        pid = program(vsid, fsid)
        self.vs = vsid
        self.fs = fsid
        self.program = pid
        self.uniforms = dict()

    def __setitem__(self, uniform, value):
        try:
            uid = self.uniforms[uniform]
        except KeyError:
            uid = gl.glGetUniformLocation(self.program, uniform)
            if uid == -1:
                raise NoSuchUniformError(uniform)
            self.uniforms[uniform] = uid

        args = [uid]
        if isinstance(value, (int, ctypes.c_int)):
            setter = gl.glUniform1i
            args.append(value)
        elif isinstance(value, (float, ctypes.c_float, ctypes.c_double)):
            setter = gl.glUniform1f
            args.append(value)
        else:
            args.extend(value)
            setter = SETTERSF[len(args) - 2]

        setter(*args)

    @property
    def id(self):
        return self.program


LP_c_char = POINTER(c_char)


class NoSuchUniformError(Exception):
    pass


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
