#!/usr/bin/python2
# -*- coding: utf-8 -*-
# Main file.

import time
import urwid
import sys
import random
import pprint
from parser import Parser

class FooterEdit(urwid.Edit):
    __metaclass__ = urwid.signals.MetaSignals
    signals = ['done']

    def keypress(self, size, key):
        if key == 'enter':
            urwid.emit_signal(self, 'done', self.get_edit_text())
            return
        elif key == 'esc':
            urwid.emit_signal(self, 'done', None)
            return

        urwid.Edit.keypress(self, size, key)

class ItemWidget(urwid.WidgetWrap):
    #def __init__ (self, id, description, color):
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
            ('fixed', 4, urwid.Padding(urwid.AttrWrap(urwid.Text(self.identifier), self.color, 'focus'), left=2)),
            (10, urwid.AttrWrap(urwid.Text('%s' % self.size), self.color, 'focus')),
            urwid.AttrWrap(urwid.Text('%s' % url.split('/')[-1]), self.color, 'focus')
        ]
        w = urwid.Columns(self.item, 1)
        self.__super.__init__(w)

    def selectable (self):
        return True

    def keypress(self, size, key):
        return key

    def sizeof_fmt(self, num, suffix='B'):
        """ https://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size """
        for unit in ['','K','M','G','T','P','E','Z']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Y', suffix)

class QGH(object):
    """ Add docstring lol """
    def __init__(self):
        # Set the palette
        self.palette = [
            ('body','dark blue', '', 'standout'),
            ('folder', 'light magenta', '', 'standout'),
            ('focus','dark red', '', 'standout'),
            ('head','light red', 'black'),
        ]

        self.parser = Parser()
        self.data   = self.parser.parse()
        leaves = self.parser.return_leaves(self.data, '__root__') ############## LEAVES
        #pprint.pprint(leaves)
        trees = self.parser.root_trees(self.data) ############## TREES
        #pprint.pprint(trees)

        # Set up class vars
        self.elements        = [] # Actual ItemWidget elements
        self.last_dir        = '' # Last directory
        self.history_pointer = 0  # Navigation history ptr

        # First sort out the directories
        i = 0
        for directory in self.parser.root_trees(self.data):
            element = ItemWidget(i, directory + '/')
            self.elements.append(element)
            i = i+1

        # Now sort out actual files.
        i = 0
        for k, v in self.parser.return_leaves(self.data, '__root__').iteritems():
            element = ItemWidget(i, k, v['size'], v['type'], v['url'])
            self.elements.append(element)
            i = i+1
            pass

        self.root_elements = self.elements # Copy this into root_elements so we can cache and restore the root tree when needed.

        # Initialize urwid!
        self.head       = urwid.AttrMap(urwid.Text('selected:'), 'head')
        self.foot       = urwid.AttrMap(urwid.Text('q Q - exit        enter- void         b - return the list'), 'head')
        self.walker     = urwid.SimpleListWalker(self.elements)
        self.listbox    = urwid.ListBox(self.walker)
        self.view       = urwid.Frame(urwid.AttrWrap(self.listbox, 'body'), header=self.head, footer=self.foot)

        loop = urwid.MainLoop(self.view, self.palette, unhandled_input=self.handle_keystroke)
        urwid.connect_signal(self.walker, 'modified', self.update)
        loop.run()

    def handle_keystroke(self, input):
        if input in ('q', 'Q'):
            raise urwid.ExitMainLoop()

        if input == 'enter':
            self.focus = self.listbox.get_focus()[0].content # Grab the focused element

            if self.focus == '../': # Go UP
                self.last_dir = self.last_dir[:-1].split('/') # Split it by /
                self.last_dir.pop() # Remove the last directory (current dir)
                self.last_dir = '/'.join(self.last_dir) + '/' # Join the rest in a list and append / because that's our dir notation.
                self.focus = self.last_dir
                if(self.focus == '/'):
                    self.last_dir = ''
                    self.handle_root_directory()
                else:
                    self.handle_directory()

                return

            elif self.focus[-1] == '/': # Must be a normal directory then!
                self.focus      = self.listbox.get_focus()[0].content
                self.focus      = self.last_dir + self.focus
                self.last_dir   = self.focus
                self.handle_directory()
                return

            #self.handle_file() # Handle the file!
            pass

        if input is 'b':
            self.listbox = urwid.ListBox(urwid.SimpleListWalker([ItemWidget(1, 'aloha/')]))
            self.view.set_body(self.listbox) #works LOOOOOOOOOOOOOOOOOOOOOL

        if input is 'e':
            self.footer_edit()

    def footer_edit(self):
        self.foot_new = FooterEdit('>> ')
        self.view.set_footer(self.foot_new)
        self.view.set_focus('footer')
        urwid.connect_signal(self.foot_new, 'done', self.edit_done)

    def edit_done(self, content = None):
        self.view.set_focus('body')
        urwid.disconnect_signal(self.foot_new, 'done', self.edit_done)
        if content:
            self.view.set_body(urwid.Filler(urwid.Text(content), 'top'))
        self.view.set_footer(self.foot)

    def update(self):
        self.focus = self.listbox.get_focus()[0].content
        #self.view.set_header(urwid.AttrWrap(urwid.Text('selected: %s' % str(self.focus)), 'head'))
        #self.view.set_footer(urwid.AttrWrap(urwid.Text('selected: %s' % str(self.focus)), 'head'))

    def handle_root_directory(self):
        # Just restore the original lol
        self.walker  = urwid.SimpleListWalker(self.root_elements)
        self.listbox = urwid.ListBox(self.walker)
        urwid.connect_signal(self.walker, 'modified', self.update)
        self.view.set_header(urwid.AttrWrap(urwid.Text('/'), 'head'))
        self.view.set_body(self.listbox)

    def handle_directory(self):
        # Grab the path
        path = self.focus[:-1]

        # Return the leaves and trees for this specific path
        trees   = self.parser.return_trees(self.data, path)
        leaves  = self.parser.return_leaves(self.data, path)

        # Set the new elements
        self.elements = []

        # First, the directories
        i = 0
        # Append ../ so we can go back lol
        self.elements.append(ItemWidget(i, '../'))
        if trees:
            for directory in trees:
                #element = ItemWidget(i, directory + '/')
                element = ItemWidget(i, directory.split('/')[-1] + '/')
                self.elements.append(element)
                i = i+1

        i = 0
        if not leaves:
            self.elements.append(ItemWidget(0, '../'))
        else:
            for k, v in leaves.iteritems():
                if not 'url' in v: continue # Not a file.
                element = ItemWidget(i, k, v['size'], v['type'], v['url'])
                self.elements.append(element)
                i = i+1
                pass

        #sys.exit()
        self.walker  = urwid.SimpleListWalker(self.elements)
        self.listbox = urwid.ListBox(self.walker)
        urwid.connect_signal(self.walker, 'modified', self.update)
        self.view.set_header(urwid.AttrWrap(urwid.Text(str(self.focus)), 'head'))
        self.view.set_body(self.listbox)

QGH()