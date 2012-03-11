# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, generators, print_function, with_statement

import json
import levelformat
import sys
import os.path
import cPickle as pickle


def print_help():
    print('Usage: {0} levelfile [levelfile ...]'.format(sys.argv[0]))
    print('Convert levels in format 1 (pickled python) to 2 (json)')


def convert(files):
    encoder = levelformat.LevelEncoder()
    for f in files:
        try:
            outf = f + '.json'
            print('{0} -> {1}'.format(f, outf))
            with open(f) as data:
                level = pickle.load(data)
            level = levelformat.LevelDescriptor(2, level.rects)
            with open(outf, 'wb') as jsondata:
                jsondata.write(encoder.encode(level))
        except Exception, e:
            print('Error trying to convert {file}: {exception}'.format(file=f, exception=e))


if __name__ == '__main__':
    files = sys.argv[1:]
    if len(files) == 0:
        print_help()
    else:
        convert(files)