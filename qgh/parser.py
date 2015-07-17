#!/usr/bin/python2
# -*- coding: utf-8 -*-
# Parser.

import json
import sys
import pprint

class Parser(object):
    """docstring for Parser"""
    def __init__(self):
        # Blah blah httpconnection, load crap....
        file = open('../data.txt', 'r')
        self.data = file.read()
        file.close()

        self.data = json.loads(self.data)

    def core_trees(self, data):
        _return = {}

        for directory in data:
            if directory == '__root__':
                # root stuff here.
                _return.update(data['__root__'])
            else:
                _return.update({directory: 'tree'})

        return _return

    def return_trees(self, data, tree):
        subdirs = tree.split('/')
        #print subdirs
        _return = []

        data = reduce(dict.get, subdirs, data)
        if not data:
            #return _return.append('(There is nothing in here)')
            return None

        for k, v in data.iteritems():
            if 'type' in data[k] and data[k]['type'] == 'blob':
                continue
            # Add to output.
            #_return.append(tree + k)
            _return.append('%s/%s' % (tree, k))
        return _return

    def return_leaves(self, data, tree):
        subdirs = tree.split('/')
        return reduce(dict.get, subdirs, data)

    def root_trees(self, data):
        _return = []
        for k, v in data.iteritems():
            if not k == '__root__': _return.append(k)

        return _return

    def count_tree(self, data, tree):
        pass

    def parse(self):
        trees = []
        blobs = {}

        for object in self.data['tree']:
            if object['type'] == 'tree': # Add to tree list
                trees.append(object['path'])
            else:
                # Add to blobs dict
                blobs.update({object['path']: {'size': str(object['size']), 'url': object['url'], 'type': object['type']}})

        # Process!
        dict = {'__root__': {}}

        for item in trees:
            p = dict
            for x in item.split('/'):
                p = p.setdefault(x, {})

        for k, v in blobs.iteritems():
            p = dict
            items = k.split('/')
            if len(items) == 1:
                p['__root__'].update({items[0]: {'size': str(v['size']), 'url': v['url'], 'type': object['type']}})
            else:
                length = len(items)-1
                i = 0
                for subdir in items:
                    if not subdir == None:
                        p = p.setdefault(subdir, {})
                        if i == length:
                            p.update({'size': str(v['size']), 'url': v['url'], 'type': v['type']})
                        i = i+1


        return dict
