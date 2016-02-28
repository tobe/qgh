#!/usr/bin/python
# -*- coding: utf-8 -*-

# Configuration class used to set colors/API key and such misc stuff.

import json
import sys
import os

class Config(object):
    """ Configuration class used to set colors/API key and such misc stuff. """
    def __init__(self):
        # Try to open the config file
        try:
            fp = open('%s/config.json' % (os.path.dirname(os.path.abspath(__file__))), 'r')
        except IOError as e:
            print('Unable to open the config.json file: ' + str(e))
            sys.exit()

        # Now try to parse it
        try:
            self.data = json.load(fp)
        except ValueError as e:
            print('Unable to load the JSON file: ' + str(e))
            sys.exit()

        fp.close() # Clear here
        self.pad_length = 3 # Padding length
        pass

    @property
    def get_version(self):
        return self.data['version']

    @property
    def get_editor(self):
        return self.data['editor']


    def get_palette(self):
        """Returns the color palette.

        """
        return [
            # Main body
            ('body', self.data['colors']['body'][0], self.data['colors']['body'][1], self.data['colors']['body'][2]),
            # A folder, subtree/dir
            ('folder', self.data['colors']['folder'][0], self.data['colors']['folder'][1], self.data['colors']['folder'][2]),
            # Element focused/selected
            ('focus', self.data['colors']['focus'][0], self.data['colors']['focus'][1], self.data['colors']['focus'][2]),
            # Footer
            ('footer', self.data['colors']['footer'][0], self.data['colors']['footer'][1], self.data['colors']['footer'][2]),
            # Header
            ('head', self.data['colors']['head'][0], self.data['colors']['head'][1], self.data['colors']['head'][2]),
            # View in footer
            ('view', self.data['colors']['view'][0], self.data['colors']['view'][1], self.data['colors']['view'][2]),
            # Focused view
            ('view_focus', self.data['colors']['view_focus'][0], self.data['colors']['view_focus'][1], self.data['colors']['view_focus'][2])
        ]

    def update_footer(self, current_view):
        self.current_view = current_view
        return [
            (self._is_focused('1: main'),  '1: main'),  ' '.center(self.pad_length),
            (self._is_focused('2: trees'), '2: trees'), ' '.center(self.pad_length),
            (self._is_focused('3: files'), '3: files'), ' '.center(self.pad_length),
        ]

        pass

    def _is_focused(self, view): return 'view_focus' if view == self.current_view else 'view'
