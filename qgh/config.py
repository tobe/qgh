#!/usr/bin/python2
# -*- coding: utf-8 -*-

# Configuration class used to set colors/API key and such misc stuff.

class Config(object):
    """ Configuration class used to set colors/API key and such misc stuff. """
    def __init__(self):
        # Read configuration file here and stuff.

        self.pad_length = 3
        pass

    def get_palette(self):
        """Returns the color palette.

        """
        return [
            # Main body
            ('body','dark blue', '', 'standout'),
            # A folder, subtree/dir
            ('folder', 'light magenta', '', 'standout'),
            # Element focused/selected
            ('focus','dark red', '', 'standout'),
            # Footer
            ('footer', 'light red', 'black', 'standout'),
            # Header
            ('head','light red', 'black'),
            # View in footer
            ('view', 'light cyan', 'black', 'underline'),
            # Focused view
            ('view_focus', 'light red', 'dark gray', 'underline')
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
