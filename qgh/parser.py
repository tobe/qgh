#!/usr/bin/python2
# -*- coding: utf-8 -*-

# Parser.

import json
import sys
import pprint
import httplib
import time
import datetime

class Parser(object):
    """Retrieves the data from the API and parses it.

    """

    def __init__(self, user, repository, branch):
        self.started = int(time.time()) # For benchmarking I guess.

        # First, get the sha_hash
        """data = self._query_api('/repos/%s/%s/git/refs/heads/%s' % (user, repository, branch))

        if not 'sha' in data['object']:
            print('Received unknown JSON. Could not find the sha hash.')
            sys.exit()

        sha_hash = data['object']['sha']
        # Inform the user about what's going on before urwid launches
        self._write_flushed('Got URL: %s' % (data['url']))
        self._write_flushed('Got SHA: %s' % (sha_hash))
        self._write_flushed('Requesting recursive project tree...')

        # Now that we've got our SHA, we can send an actual request for the repository tree
        self.data = self._query_api('https://api.github.com/repos/%s/%s/git/trees/%s?recursive=1' % (user, repository, sha_hash))"""

        # Just display some statistics.
        self.time_taken = datetime.datetime.fromtimestamp(int(time.time())-self.started).strftime('%-Mm %ss')
        self._write_flushed('Done, took me %s' % self.time_taken)

        with open('data.txt', 'r') as ff:
            self.data = json.loads(ff.read())
            ff.close()

    def _write_flushed(self, data):
        """Writes to stdout and then flushes the output for live updates about fetching data.

        Args:
            data: What to print out to stdout.

        """
        sys.stdout.write('%s\n' % (data))
        sys.stdout.flush()

    def _query_api(self, url):
        """Queries the Github API and returns a JSON parsed string.

        Args:
            url: Full API url request.

        """
        try:
            # Create a HTTPLib object
            conn = httplib.HTTPSConnection('api.github.com')

            # Define the UA, because Github asks so.
            headers = {'User-Agent': 'qgh/1.0'}

            # Try to retrieve the sha of the given repository
            conn.request('GET', url, headers=headers)

            # Get the response
            response = conn.getresponse()

            # Query the status code
            if response.status != 200:
                raise httplib.HTTPException('Did not receive 200 OK, received %s %s instead. Exiting...' % (str(response.status), response.reason))

            # Read and decode the data, find the hash.
            data = response.read()
            if not data or len(data) == 0:
                raise httplib.HTTPException('No data received, len(data) = %d', len(data))

            data = json.loads(data)
            return data
        except httplib.HTTPException as e:
            print 'HTTPLib error: %s\nFailed lookup for URL %s' % str(e, url)
            sys.exit()

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

        _return.sort()
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