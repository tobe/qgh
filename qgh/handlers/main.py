#!/usr/bin/python
# -*- coding: utf-8 -*-

# Main handler?

import urwid
import os
import base64
import subprocess

class ItemWidget(urwid.WidgetWrap):
    """Class used for handling each item in the SimpleListWalker walker.

        Args:
            id: The ID of the item passed. This is usually a natural number.
            title: The main item contents, such as the filename or the directory/tree name
            size: The size of the file, if a file. Otherwise, what to show if it's not a file, such as a dir.
            type: The type of the item passed. This can either be 'blob' for a file, or 'tree' for a tree.
            url: The hash of the file, if a file. Otherwise, what to show if it's not a file. Must append "/".

        """
    def __init__(self, id, title, size = 'ー', type = 'tree', url = '/ー'):
        self.id         = id
        self.content    = '%s' % title
        self.identifier = 'F'    if type == 'blob' else 'D'
        self.color      = 'body' if type == 'blob' else 'folder'
        self.size       = size
        if size.isdigit():
            self.size   = self.sizeof_fmt(int(size))

        self.item = [
            urwid.AttrWrap(urwid.Text('%s' % title), self.color, 'focus'),
            ('fixed', 4, urwid.Padding(urwid.Text(self.identifier), left=2)),
            (10, urwid.Text('%s' % self.size)),
            urwid.Text('%s' % url.split('/')[-1]),
        ]

        w = urwid.AttrMap(urwid.Columns(self.item, 1), 'body', 'focus')
        self.__super.__init__(w)

    def selectable (self):
        """Makes the items selectable.

        Returns: true

        """
        return True

    def keypress(self, size, key):
        """Handle the keypress.

        Args:
            size: The size of the widget
            key: The key that has been pressed

        """
        #print('KEYPRESS: %s' % key)
        return key

    def sizeof_fmt(self, num, suffix='B'):
        """Convert bytes to human file sizes.

        Args:
            num: The number to convert.
            suffix: The suffix to use.

        Source/Original: https://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size """
        for unit in ['','K','M','G','T','P','E','Z']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Y', suffix)


class MainHandler:
    """ add doc here """
    def __init__(self, qgh):
        self.QGH = qgh

    def handle_root_directory(self):
        """Restores the original root directory contents when called.

        """
        self.QGH.elements = self.QGH.root_elements # Restore the root directory structure
        self.QGH.walker   = urwid.SimpleListWalker(self.QGH.root_elements)
        self.QGH.listbox  = urwid.ListBox(self.QGH.walker)
        self.QGH.focus    = '/' # Restore focus
        self.QGH.last_dir = '' # Restore last directory

        urwid.connect_signal(self.QGH.walker, 'modified', self.QGH.update)

        self.QGH.view.set_header(urwid.AttrWrap(urwid.Columns([
            urwid.Text('/', align='left'),
            urwid.Text('%s item(s)' % (len(self.QGH.root_elements)), align='right')
        ]), 'head'))

        self.QGH.view.set_body(self.QGH.listbox)

    def handle_directory(self):
        """Handles the given directory, and displays it.

        """
        # Grab the path
        path = self.QGH.focus[:-1]

        # Return the leaves and trees for this specific path
        trees   = self.QGH.Parser.return_trees(self.QGH.data, path)
        leaves  = self.QGH.Parser.return_leaves(self.QGH.data, path)

        # Set the new elements
        self.QGH.elements = []

        # First, the directories
        i = 0
        self.QGH.elements.append(ItemWidget(i, '../')) # Append ../ so we can go back lol
        if trees:
            for directory in sorted(trees):
                #element = ItemWidget(i, directory + '/')
                element = ItemWidget(i, directory.split('/')[-1] + '/') # We're just interested in the last subdir. And just append / to it.
                self.QGH.elements.append(element)
                i = i+1

        i = 0
        if not leaves:
            self.QGH.elements.append(ItemWidget(0, '../'))
        else:
            for k, v in sorted(leaves.items()):
                if not 'url' in v: continue # Not a file. Skipped!
                element = ItemWidget(i, k, v['size'], v['type'], v['url'])
                self.QGH.elements.append(element)
                i = i+1
                pass

        # Set the walker and the listbox...
        self.QGH.walker  = urwid.SimpleListWalker(self.QGH.elements)
        self.QGH.listbox = urwid.ListBox(self.QGH.walker)

        # Connect the signal so that we can update the header/footer later.
        urwid.connect_signal(self.QGH.walker, 'modified', self.QGH.update)

        # Set the header to the current directory so the user knows where they are. Also display how many items are there.
        self.QGH.view.set_header(urwid.AttrWrap(urwid.Columns([
            urwid.Text(str(self.QGH.focus), align='left'),
            urwid.Text('%s item(s)' % (len(leaves)), align='right')
        ]), 'head'))

        # Finally, set the body.
        self.QGH.view.set_body(self.QGH.listbox)