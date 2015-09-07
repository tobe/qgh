#!/usr/bin/python
# -*- coding: utf-8 -*-

# Main file and main classes.

import time
import urwid
import argparse
import re
import parser
import config
from main_handler import MainHandler, ItemWidget

class AppError(Exception):
    pass

class FooterEdit(urwid.Edit, metaclass=urwid.signals.MetaSignals):
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

class QGH(MainHandler):
    """Main class, used to initialize qgh.

    """
    def __init__(self):
        # Grab the user/repository
        arg_parser = argparse.ArgumentParser(description='Console curses browser for github repo contents.')
        arg_parser.add_argument('remote', help='Remote repository in the following format: user/branch. Example: infyhr/qgh')
        arg_parser.add_argument('branch', nargs='?', default='master', help='The branch to look up. By default this is "master".')
        args = arg_parser.parse_args()

        # Set the palette
        self.config  = config.Config()
        self.palette = self.config.get_palette()

        # See if we can find / in the remote argument.
        if '/' not in args.remote:
            raise AppError('Remote user/repository supplied in wrong format. Cannot find "/".')

        # Split it by / so we can determine the user and the branch itself.
        remote = args.remote.split('/')

        # Set them here
        self.user       = remote[0]
        self.repository = remote[1]
        self.branch     = args.branch

        # Pass it onto the Parser object.
        self.parser = parser.Parser(self.user, self.repository, self.branch)
        # Grab the data
        self.data = self.parser.parse()
        # Grab leaves from the data
        leaves = self.parser.return_leaves(self.data, '__root__')
        # Grab trees from the data
        trees = self.parser.root_trees(self.data)

        # Set up class vars
        self.elements        = [] # Actual ItemWidget elements
        self.last_dir        = '' # Last directory. Used for everything pretty much.
        self.current_dir     = None # Current directory. Used for resetting focus.
        self.current_view    = '1: main' # Current view
        self.last_id         = 0 # Last ID of the previous directory (ItemWalker)

        # Grab the directories from the root project and pass them onto the ItemWidget
        i = 0
        for directory in self.parser.root_trees(self.data):
            element = ItemWidget(i, directory + '/')
            self.elements.append(element)
            i = i+1

        # Now do the same for files.
        i = 0
        for k, v in sorted(self.parser.return_leaves(self.data, '__root__').items()):
            element = ItemWidget(i, k, v['size'], v['type'], v['url'])
            self.elements.append(element)
            i = i+1
            pass

        # Copy this into root_elements so we can cache and restore the root tree when needed.
        self.root_elements = self.elements

        # Initialize urwid!
        self.head       = urwid.AttrMap(urwid.Text('selected:'), 'head')
        footer_text     = ['qgh 1.0 ー', ' %s' % (self.parser.time_taken)]
        self.foot       = urwid.AttrMap(urwid.Text(footer_text), 'footer')
        self.walker     = urwid.SimpleListWalker(self.elements)
        self.listbox    = urwid.ListBox(self.walker)
        self.view       = urwid.Frame(urwid.AttrWrap(self.listbox, 'body'), header=self.head, footer=self.foot)

        # Set the header to show root.
        self.view.set_header(urwid.AttrWrap(urwid.Columns([
            urwid.Text('/', align='left'),
            urwid.Text('%s item(s)' % (len(self.root_elements)), align='right')
        ]), 'head'))

        self.loop = urwid.MainLoop(self.view, self.palette, unhandled_input=self.handle_keystroke)
        urwid.connect_signal(self.walker, 'modified', self.update)

        #self.main_handler = MainHandler()

        self.loop.run()

    def handle_keystroke(self, input):
        """Handles keystrokes in the main interface and then runs the needed function.

        Args:
            input: The keystroke itself.

        """
        self.focus = self.listbox.get_focus()[0].content # Grab the focused element

        if input in ('q', 'Q'):
            raise urwid.ExitMainLoop()

        if input == '1':
            self.current_view = '1: main'
            self.update()
            self.handle_root_directory()

        if input == '2':
            self.current_view = '2: trees'
            self.update()
            self.handle_trees()

        if input == '3':
            self.current_view = '3: files'
            self.update()
            self.handle_files()

        if input == 'enter':
            if self.focus != '../': self.current_dir = self.focus # Set the current directory.

            # Go UP
            if self.focus == '../':
                self.last_dir    = self.last_dir[:-1].split('/') # Split it by /
                self.current_dir = self.last_dir[-1] # Set the current directory
                self.last_dir.pop() # Remove the last directory (current dir) so we can preserve history

                # Join the rest in a list and append / because that's our dir notation.
                self.last_dir = '/'.join(self.last_dir) + '/'
                self.focus = self.last_dir # Set the focus to the last used directory.

                if(self.focus == '/'): # If we're dealing with the root tree/directory...
                    self.last_dir = '' # Set the last_dir to nothing because it's root. Next SUB directory will append to this.
                    self.handle_root_directory() # Then handle it accordingly.
                else:
                    self.handle_directory() # It's not root dir, handle it normally.

                # Reset focus
                self.reset_focus()
                return

            # Ends with /, must be a 'normal' directory then.
            elif self.focus[-1] == '/':
                self.focus      = self.listbox.get_focus()[0].content # Grab the current focus
                self.focus      = self.last_dir + self.focus # Set the focus to include the last directory + currently focused directory.
                self.last_dir   = self.focus # And the last directory used is the currently focused one. Simple as that (lol, not really).
                self.handle_directory() # Handle the directory here.
                return

            # It's not a directory nor we're moving up a level. So it's a file then?
            self.handle_file()
            pass

        # also vi-like
        if input == 'g':
            self.listbox.set_focus(0)

        # vi-like
        if input == 'G':
            self.listbox.set_focus(len(self.elements)-1)

        # Testing, plz ignore.
        if input is 'e':
            self.footer_edit()

        # Redraw
        if input in ('r', 'R'):
            self.loop.draw_screen()

        # vi nagivation
        if input in ('k', 'K'):
            widget, current_position = self.walker.get_focus()
            try:
                widget, previous_position = self.walker.get_prev(current_position)
                self.walker.set_focus(previous_position)
            except IndexError: # We are at the very beginning. Nothing to do here.
                pass

        # vi navigation
        if input in ('j', 'J'):
            widget, current_position = self.walker.get_focus()
            try:
                widget, next_position = self.walker.get_next(current_position)
                self.walker.set_focus(next_position)
            except IndexError: # We are at the very end. Nothing to do here.
                pass

        # search for next find-next
        if input == 'n':
            if self.search_ptr == -1: return # Nothing to search for man!

            self.search_ptr += 1 # Bump the ptr
            try: # If it actually points to an element...
                self.listbox.set_focus(self.matches[self.search_ptr])
            except IndexError:
                pass

            if self.search_ptr >= len(self.matches): # Focus the first element
                self.search_ptr = 0
                self.listbox.set_focus(self.matches[0])

        # search for prev find-prev
        if input == 'N':
            if self.search_ptr == -1: return # Nothing to search for man!

            self.search_ptr -= 1 # Lower the ptr
            try:
                self.listbox.set_focus(self.matches[self.search_ptr])
            except IndexError:
                pass

            if self.search_ptr < 0: # Focus the last element
                self.search_ptr = len(self.matches)-1
                self.listbox.set_focus(self.matches[self.search_ptr])

        # Search
        if input is '/':
            self.footer_edit(True)

    def reset_focus(self, search_for=None):
        # No search_for specified, let's assume we're looking for the current_dir
        if not search_for:
            search_for = self.current_dir + '/'

        # Otherwise, we have something things to do. Loop through elements until we find out our focus.
        n = 0
        for i in self.elements:
            if i.content == search_for:
                self.listbox.set_focus(n) # Set it here.
            n += 1

    def footer_edit(self, search = False):
        """Handles any user footer editing.

        """
        prefix = ':' if not search else 'quick find: '
        self.foot_new = FooterEdit(prefix)
        self.view.set_footer(self.foot_new)
        self.view.set_focus('footer')
        if not search:
            urwid.connect_signal(self.foot_new, 'done', self.edit_done)
        else:
            urwid.connect_signal(self.foot_new, 'done', self.go_search)

    def go_search(self, what_for):
        # Set the focus back to body
        self.view.set_focus('body')

        # Disconnect
        urwid.disconnect_signal(self.foot_new, 'done', self.go_search)

        # Check if we got a query...
        if not what_for: return

        # Construct a regex (yeah...)
        pattern = r'(.*)' + re.escape(what_for) + r'(.*)'

        # Store elements that match the query
        self.matches = []

        # Loop and match
        n = 0
        for i in self.elements:
            m = re.search(pattern, i.content, re.IGNORECASE)
            if m:
                #self.listbox.set_focus(n)
                #break
                self.matches.append(n)
            n = n+1

        # Now jump to the first match and then later we can use n N to go around
        if self.matches:
            self.listbox.set_focus(self.matches[0])

            # Set the search pointer to point to the first element.
            self.search_ptr = 0
        else:
            self.search_ptr = -1

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
        footer_data = self.config.update_footer(self.current_view)
        self.view.set_footer(urwid.AttrWrap(urwid.Text(footer_data, align='center'), 'footer', 'focus'))

if __name__ == '__main__':
    try:
        QGH()
    except KeyboardInterrupt:
        print('^C caught, exiting...')
    except ValueError as e:
        print(('ValueError: ' + str(e)))
    except AppError as e:
        print(('qgh error: ' + str(e)))
