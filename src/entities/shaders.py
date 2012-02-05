# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, generators, print_function, with_statement

import pyglet
import pyglet.gl
from pyglet import gl

import util


_PSYCHO_VS_SRC = r'''
#version 120

varying vec2 p;
const vec2 scaling_factor = vec2(0.08, 0.12);

void main() {
    p = gl_Vertex.xy * scaling_factor;
    vec4 pos = gl_ModelViewProjectionMatrix * gl_Vertex;
    gl_Position = pos;
}
'''


_PSYCHO_FS_SRC = r'''
#version 120

uniform sampler1D palette;

uniform float perturb = 0.0;

varying vec2 p;

const vec4 base_color = vec4(0.89, 0.0, 0.0, 1.0);
const vec4 white = vec4(1.0, 1.0, 1.0, 1.0);
const float xfactor = 0.06 / 0.04;
const int N = 8;

// linear
float poly1(float x) {
    return abs(x);
}

// quadratic
float poly2(float x) {
    return (x - 1.0) * (x + 1.0) + 1.0;
//    return x * (abs(x) -1.0) * 2.0 + 0.5;
}

// cubic
float poly3(float x) {
    float invmaxhalf = 0.5 / 0.5773502691896;
    float y = 0.5 + (x + 1) * x * (x - 1) * invmaxhalf;
    return y;
}

// return x within (-1, 1)
// for x = 0 returns 1.0
// for x = 0.5 returns 0
float roll(float x) {
    return (0.5 - fract(x)) * 2.0;
}

void main() {
    float p1 = 23.0, p2 = 11.0, p3 = 109.0, p4 = 41.0;
    float period = p1 * p2 * p3 * p4 / 2000.0;
    vec2 n[N];
    n[0] = vec2(0.5, 0.015);
    n[1] = vec2(0.5015, 0.05);
    n[2] = vec2(0.04, 0.5);
    n[3] = vec2(0.0325, 0.565);
    n[4] = vec2(0.003, 0.005);
    n[5] = vec2(0.008, 0.0015);
    n[6] = vec2(0.0, 0.0);
    n[7] = vec2(0.0, 0.0);

    float x[N];
    for (int i = 0; i < N; i++)
        x[i] = roll(dot(n[i], p));

    float y[N];
    float z[N];
    for (int i = 0; i < N; i++) {
        y[i] = poly1(x[i]);
    }

    //float x3 = roll(-0.714143 * p.x + 0.7 * p.y);
    //float x4 = roll(0.7 * p.x + 0.714143 * p.y);
    float a = (y[0] + y[1] + y[2] + y[3]) * 0.15 + y[4] * y[5] * 0.85;
    //a *= poly3(x[2]) * poly3(x[3]);
    gl_FragColor = texture1D(palette, fract(a + perturb));
}
'''

psycho = lambda: util.GLProgram(_PSYCHO_VS_SRC, _PSYCHO_FS_SRC)


_WALL_VS_SRC = r'''
#version 120

attribute vec2 p;

void main() {
    gl_Position = gl_ModelViewProjectionMatrix * vec4(p, 0.0, 1.0);
}
'''

_WALL_FS_SRC = r'''
#version 120

uniform vec4 color = vec4(0.0, 0.0, 0.89, 1.0);

void main() {
    gl_FragColor = color;
}
'''

wall = lambda: util.GLProgram(_WALL_VS_SRC, _WALL_FS_SRC)


_SPRITE_VS_SRC = r'''
#version 120

attribute vec4 data;

varying vec2 texcoord;

void main() {
    gl_Position = gl_ModelViewProjectionMatrix * vec4(data.xy, 0.0, 1.0);
    texcoord = data.zw;
}
'''

_SPRITE_FS_SRC = r'''
#version 120

uniform sampler2D texture;

varying vec2 texcoord;

void main() {
    gl_FragColor = texture2D(texture, texcoord);
}
'''

sprite = lambda: util.GLProgram(_SPRITE_VS_SRC, _SPRITE_FS_SRC);
