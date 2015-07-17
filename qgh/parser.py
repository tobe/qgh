#!/usr/bin/python2
# -*- coding: utf-8 -*-
# Parser.

import json
import sys
import pprint

class Parser(object):
    """Retrieves the data from the API and parses it.

    """
    def __init__(self):
        # Blah blah httpconnection, load crap....
        file = open('../data.txt', 'r')
        self.data = file.read()
        file.close()

        self.data = json.loads(self.data)

    def core_trees(self, data):
        """Returns the core project directory tree structure.

        Args:
            data: The actual data to retrieve the root directory from.

        """
        _return = {}

        for directory in data:
            if directory == '__root__':
                # root stuff here.
                _return.update(data['__root__'])
            else:
                _return.update({directory: 'tree'})

        return _return

    def return_trees(self, data, tree):
        """Returns any subtree from the dictionary data.

        Args:
            data: The dictionary to retrieve items from.
            tree: What tree to retrieve?

        """
        subdirs = tree.split('/')
        _return = []

        data = reduce(dict.get, subdirs, data)
        if not data: # If there is nothing return None. How convenient.
            return None

        for k, v in data.iteritems():
            if 'type' in data[k] and data[k]['type'] == 'blob':
                continue
            # Add to output.
            #_return.append(tree + k)
            _return.append('%s/%s' % (tree, k)) # Return the full absolute path which will get spliced later on.
        return _return

    def return_leaves(self, data, tree):
        """Returns any leaves (trees AND files) from the dictionary data.

        Args:
            data: The dictionary to retrieve items from.
            tree: What tree to retrieve?

        """
        subdirs = tree.split('/')
        return reduce(dict.get, subdirs, data)

    def root_trees(self, data):
        """Returns the root tree.

        Args:
            data: The dictionary to retrieve items from.

        """
        _return = []
        for k, v in data.iteritems():
            if not k == '__root__': _return.append(k)

        return _return

    def count_tree(self, data, tree):
        """Counts how many files there are in a given tree.

        Args:
            data: The dictionary to retrieve items from.
            tree: What tree to retrieve?

        """
        pass

    def parse(self):
        """Parses JSON to infinite level dictionaries.

        """
        trees = [] # Directories
        blobs = {} # Files

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