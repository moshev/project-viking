# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, generators, print_function, with_statement
import ctypes
from ctypes import c_int, c_uint, byref, POINTER
import numpy
import pyglet.gl
from pyglet import gl


__all__ = ['GLBuffer']


c_intp = POINTER(c_int)
c_uintp = POINTER(c_uint)


class _GLBufferContext(object):
    '''A context manager which binds an OpenGL buffer on entry
    and restores state on exit.'''


    def __init__(self, bufid):
        '''bufid - a valid OpenGL buffer object id'''

        self.bufid = bufid
        self.previd = c_uint(0)
        self.entrycount = 0


    def __enter__(self):
        if self.entrycount == 0:
            gl.glGetIntegerv(gl.GL_ARRAY_BUFFER_BINDING, ctypes.cast(byref(self.previd), c_intp))
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.bufid)
        self.entrycount += 1


    def __exit__(self, exc_type, exc_value, traceback):
        self.entrycount -= 1
        if self.entrycount == 0:
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.previd)


class GLBuffer(object):
    '''Abstracts an OpenGL buffer object with a defined datatype.
    Automatically resizes when adding data.'''

    def __init__(self, size=0, dtype=numpy.float32, usage=gl.GL_DYNAMIC_DRAW):
        '''
        size - how much storage to allocate for this buffer in advance (in items, not bytes)
        dtype - type of items in storage (float, float16, float32, int, etc.)
        usage - one of GL_{STREAM,STATIC,DYNAMIC}_{READ,COPY,DRAW}
        Description copied from OpenGL reference pages:

        The frequency of access may be one of these:
        STREAM
            The data store contents will be modified once and used at most a few times.
        STATIC
            The data store contents will be modified once and used many times.
        DYNAMIC
            The data store contents will be modified repeatedly and used many times.

        The nature of access may be one of these:

        DRAW
            The data store contents are modified by the application,
            and used as the source for GL drawing and image specification commands.
        READ
            The data store contents are modified by reading data from the GL,
            and used to return that data when queried by the application.
        COPY
            The data store contents are modified by reading data from the GL,
            and used as the source for GL drawing and image specification commands.'''

        self.usage = usage
        self.dtype = numpy.dtype(dtype)
        bufid = ctypes.c_uint(0)
        gl.glGenBuffers(1, ctypes.byref(bufid))
        self.bufid = bufid
        self.bound = _GLBufferContext(self.bufid)
        if size > 0:
            with self.bound:
                gl.glBufferData(gl.GL_ARRAY_BUFFER, size * self.dtype.itemsize,
                                None, self.usage)


    def __len__(self):
        with self.bound:
            size = c_int(0)
            gl.glGetBufferParameteriv(gl.GL_ARRAY_BUFFER, gl.GL_BUFFER_SIZE, byref(size))
            return size.value // self.dtype.itemsize


    def __getitem__(self, key):
        with self.bound:
            if isinstance(key, slice):
                start = int(key.start)
                stop = int(key.stop)
            else:
                start = int(key)
                stop = start + 1
            sz = len(self)
            if start < 0 or start >= sz or stop < 0 or stop > sz or start >= stop:
                raise IndexError
            shape = (stop - start,)
            a = numpy.empty(shape=shape, dtype=self.dtype)
            gl.glGetBufferSubData(gl.GL_ARRAY_BUFFER, start * self.dtype.itemsize,
                                  (stop - start) * self.dtype.itemsize, a.ctypes.data)
            return a


    def __setitem__(self, key, value):
        with self.bound:
            sz = len(self)
            if isinstance(key, slice):
                start = int(key.start) if key.start is not None else 0
                stop = int(key.stop) if key.stop is not None else start + value.size
            else:
                start = int(key)
                stop = start + 1
            if start < 0 or stop < 0 or start >= stop:
                raise IndexError
            if stop > sz:
                newsz = max(sz * 2, stop)
                a = numpy.empty((newsz,), dtype=self.dtype)
                # intel dies when querying an empty buffer :[
                if sz > 0:
                    gl.glGetBufferSubData(gl.GL_ARRAY_BUFFER, 0,
                                          sz * self.dtype.itemsize,
                                          a.ctypes.data)
                b = numpy.asarray(value).reshape(-1)
                a[start:stop] = b
                gl.glBufferData(gl.GL_ARRAY_BUFFER, newsz * self.dtype.itemsize,
                                a.ctypes.data, self.usage)
            else:
                a = numpy.ascontiguousarray(value, self.dtype).reshape(-1)
                sz = min((stop - start), len(a))
                gl.glBufferSubData(gl.GL_ARRAY_BUFFER, start * self.dtype.itemsize,
                                   sz * self.dtype.itemsize, a.ctypes.data)
