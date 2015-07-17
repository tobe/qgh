#!/usr/bin/python2
# -*- coding: utf-8 -*-

# Main file and main classes.

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
        """Handle the keypress when editing the footer interface.

        Args:
            size: The size of the widget
            key: The key that has been pressed

        """
        if key == 'enter':
            urwid.emit_signal(self, 'done', self.get_edit_text())
            return
        elif key == 'esc':
            urwid.emit_signal(self, 'done', None)
            return

        urwid.Edit.keypress(self, size, key)

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
            ('fixed', 4, urwid.Padding(urwid.AttrWrap(urwid.Text(self.identifier), self.color, 'focus'), left=2)),
            (10, urwid.AttrWrap(urwid.Text('%s' % self.size), self.color, 'focus')),
            urwid.AttrWrap(urwid.Text('%s' % url.split('/')[-1]), self.color, 'focus')
        ]
        w = urwid.Columns(self.item, 1)
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

class QGH(object):
    """Main class, used to initialize qgh.

    """
    def __init__(self):
        # Set the palette
        self.palette = [
            ('body','dark blue', '', 'standout'),
            ('folder', 'light magenta', '', 'standout'),
            ('focus','dark red', '', 'standout'),
            ('head','light red', 'black'),
        ]

        # Delare the parser class
        self.parser = Parser()
        # Grab the data
        self.data   = self.parser.parse()
        # Grab leaves from the data
        leaves = self.parser.return_leaves(self.data, '__root__')
        # Grab trees from the data
        trees = self.parser.root_trees(self.data)

        # Set up class vars
        self.elements        = [] # Actual ItemWidget elements
        self.last_dir        = '' # Last directory

        # Grab the directories from the root project and pass them onto the ItemWidget
        i = 0
        for directory in self.parser.root_trees(self.data):
            element = ItemWidget(i, directory + '/')
            self.elements.append(element)
            i = i+1

        # Now do the same for files.
        i = 0
        for k, v in self.parser.return_leaves(self.data, '__root__').iteritems():
            element = ItemWidget(i, k, v['size'], v['type'], v['url'])
            self.elements.append(element)
            i = i+1
            pass

        # Copy this into root_elements so we can cache and restore the root tree when needed.
        self.root_elements = self.elements

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
        """Handles keystrokes in the main interface and then runs the needed function.

        Args:
            input: The keystroke itself.

        """
        if input in ('q', 'Q'):
            raise urwid.ExitMainLoop()

        if input == 'enter':
            self.focus = self.listbox.get_focus()[0].content # Grab the focused element

            # Go UP
            if self.focus == '../':
                self.last_dir = self.last_dir[:-1].split('/') # Split it by /
                self.last_dir.pop() # Remove the last directory (current dir)

                # Join the rest in a list and append / because that's our dir notation.
                self.last_dir = '/'.join(self.last_dir) + '/'
                self.focus = self.last_dir # Set the focus to the last used directory.

                if(self.focus == '/'): # If we're dealing with the root tree/directory...
                    self.last_dir = '' # Set the last_dir to nothing because it's root. Next SUB directory will append to this.
                    self.handle_root_directory() # Then handle it accordingly.
                else:
                    self.handle_directory() # It's not root dir, handle it normally.

                return

            # Ends with /, must be a 'normal' directory then.
            elif self.focus[-1] == '/':
                self.focus      = self.listbox.get_focus()[0].content # Grab the current focus
                self.focus      = self.last_dir + self.focus # Set the focus to include the last directory + currently focused directory.
                self.last_dir   = self.focus # And the last directory used is the currently focused one. Simple as that (lol, not really).
                self.handle_directory() # Handle the directory here.
                return

            # It's a file! Do its thing here.
            # infy@A780LM-M: this should popen or something where user wants.
            #self.handle_file() # Handle the file!
            pass

        # Testing, plz ignore
        if input is 'b':
            pass
            #self.listbox = urwid.ListBox(urwid.SimpleListWalker([ItemWidget(1, 'aloha/')]))
            #self.view.set_body(self.listbox) #works LOOOOOOOOOOOOOOOOOOOOOL

        # Testing!
        if input is 'e':
            self.footer_edit()

    def footer_edit(self):
        """Handles any user footer editing.

        """
        self.foot_new = FooterEdit('>> ')
        self.view.set_footer(self.foot_new)
        self.view.set_focus('footer')
        urwid.connect_signal(self.foot_new, 'done', self.edit_done)

    def edit_done(self, content = None):
        """After footer editing process is pointed here.

        Args:
            content: The content, what user entered, if any.

        """
        self.view.set_focus('body')
        urwid.disconnect_signal(self.foot_new, 'done', self.edit_done)
        if content:
            self.view.set_body(urwid.Filler(urwid.Text(content), 'top'))
        self.view.set_footer(self.foot)

    def update(self):
        """Called whenever the walker updates, e.g. user presses key.

        """
        self.focus = self.listbox.get_focus()[0].content
        #self.view.set_header(urwid.AttrWrap(urwid.Text('selected: %s' % str(self.focus)), 'head'))
        #self.view.set_footer(urwid.AttrWrap(urwid.Text('selected: %s' % str(self.focus)), 'head'))

    def handle_root_directory(self):
        """Restores the original root directory contents when called.

        """
        self.walker  = urwid.SimpleListWalker(self.root_elements)
        self.listbox = urwid.ListBox(self.walker)

        urwid.connect_signal(self.walker, 'modified', self.update)

        self.view.set_header(urwid.AttrWrap(urwid.Text('/'), 'head'))
        self.view.set_body(self.listbox)

    def handle_directory(self):
        """Handles the given directory, and displays it.

        """
        # Grab the path
        path = self.focus[:-1]

        # Return the leaves and trees for this specific path
        trees   = self.parser.return_trees(self.data, path)
        leaves  = self.parser.return_leaves(self.data, path)

        # Set the new elements
        self.elements = []

        # First, the directories
        i = 0
        self.elements.append(ItemWidget(i, '../')) # Append ../ so we can go back lol
        if trees:
            for directory in trees:
                #element = ItemWidget(i, directory + '/')
                element = ItemWidget(i, directory.split('/')[-1] + '/') # We're just interested in the last subdir. And just append / to it.
                self.elements.append(element)
                i = i+1

        i = 0
        if not leaves:
            self.elements.append(ItemWidget(0, '../'))
        else:
            for k, v in leaves.iteritems():
                if not 'url' in v: continue # Not a file. Skipped!
                element = ItemWidget(i, k, v['size'], v['type'], v['url'])
                self.elements.append(element)
                i = i+1
                pass

        # Set the walker and the listbox...
        self.walker  = urwid.SimpleListWalker(self.elements)
        self.listbox = urwid.ListBox(self.walker)

        # Connect the signal so that we can update the header/footer later.
        urwid.connect_signal(self.walker, 'modified', self.update)

        # Set the header to the current directory so the user knows where they are.
        self.view.set_header(urwid.AttrWrap(urwid.Text(str(self.focus)), 'head'))

        # Finally, set the body.
        self.view.set_body(self.listbox)

QGH()