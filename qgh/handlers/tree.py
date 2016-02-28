#!/usr/bin/python
# -*- coding: utf-8 -*-

# Main handler?

import urwid
import os
import base64
import subprocess
import webbrowser

class ItemWidget(urwid.WidgetWrap):
    """Class used for handling each item in the SimpleListWalker walker for trees.

        Args:
            id: The ID of the item passed. This is usually a natural number.
            title: The main item contents, such as the filename or the directory/tree name

    """
    def __init__(self, id, title, qgh):
        self.id         = id
        self.content    = '%s' % title
        self.identifier = 'D'
        self.color      = 'folder'
        self.QGH        = qgh

        self.item = [
            urwid.AttrWrap(urwid.Text('%s' % title), self.color, 'focus'),
            urwid.AttrWrap(urwid.Text('%s' % self.identifier), 'body')
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
        if key in ('o', 'O'):
            webbrowser.open('https://www.github.com/%s/%s/tree/%s/%s' % (self.QGH.user, self.QGH.repository, self.QGH.branch, self.content))

        return key

class TreeHandler():
    def __init__(self, qgh):
        self.QGH = qgh

    def handle_trees(self):
        # Reset the focus and the last directory since we're viewing trees and not a single directory
        self.QGH.focus    = '/'
        self.QGH.last_dir = '' # Otherwise, we wouldn't be able to jump to dir view

        # Wipe all the elements and populate with trees only.
        self.QGH.elements = []
        all_trees = self.QGH.Parser.all_trees();

        # Construct an itemlist
        i = 0
        for directory in sorted(all_trees):
            element  = ItemWidget(i, directory + '/', self.QGH)
            self.QGH.elements.append(element)
            i = i+1

        # Set up the walker
        self.QGH.walker  = urwid.SimpleListWalker(self.QGH.elements)
        self.QGH.listbox = urwid.ListBox(self.QGH.walker)

        # Connect the signal so that we can update the header/footer later.
        urwid.connect_signal(self.QGH.walker, 'modified', self.QGH.update)

        # Fix the header
        self.QGH.view.set_header(urwid.AttrWrap(urwid.Columns([
            urwid.Text('/', align='left'), # fakeroot
            urwid.Text('%s item(s)' % (len(self.QGH.elements)), align='right')
        ]), 'head'))

        self.QGH.view.set_body(self.QGH.listbox)