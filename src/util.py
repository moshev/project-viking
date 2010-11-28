from __future__ import print_function, absolute_import
import sys
import os
import numpy
import pygame.image
import cPickle as pickle
import components

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
    return os.path.normpath(os.path.join(os.path.dirname(sys.argv[0]), '..', 'data'))

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

