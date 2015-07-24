#!/usr/bin/python2
# -*- coding: utf-8 -*-

# Main file and main classes.

import time
import urwid
import sys
import random
import pprint
import argparse
import subprocess
import base64
import os
import re
from parser import Parser
from config import Config

class AppError(Exception):
    pass

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
        # Grab the user/repository
        arg_parser = argparse.ArgumentParser(description='Console curses browser for github repo contents.')
        arg_parser.add_argument('remote', help='Remote repository in the following format: user/branch. Example: infyhr/qgh')
        arg_parser.add_argument('branch', nargs='?', default='master', help='The branch to look up. By default this is "master".')
        args = arg_parser.parse_args()

        # Set the palette
        self.config  = Config()
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
        self.parser = Parser(self.user, self.repository, self.branch)
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
        for k, v in sorted(self.parser.return_leaves(self.data, '__root__').iteritems()):
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

        # Testing, plz ignore.
        if input is 'e':
            self.footer_edit()

        # Redraw
        if input in ('r', 'R'):
            self.loop.draw_screen()

        # J/K
        if input in ('k', 'K'):
            widget, current_position = self.walker.get_focus()
            try:
                widget, previous_position = self.walker.get_prev(current_position)
                self.walker.set_focus(previous_position)
            except IndexError: # We are at the very beginning. Nothing to do here.
                pass

        # J/K
        if input in ('j', 'J'):
            widget, current_position = self.walker.get_focus()
            try:
                widget, next_position = self.walker.get_next(current_position)
                self.walker.set_focus(next_position)
            except IndexError: # We are at the very end. Nothing to do here.
                pass

        # Search
        if input is '/':
            self.footer_edit(True)

    def reset_focus(self, search_for=None):
        # No search_for specified, let's assume we're looking for the current_dir
        if not search_for: search_for = self.current_dir

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
        self.foot_new = FooterEdit('>> ')
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

        # Loop and match
        n = 0
        for i in self.elements:
            m = re.search(pattern, i.content, re.IGNORECASE)
            if m:
                self.listbox.set_focus(n)
                break
            n = n+1

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

    def handle_root_directory(self):
        """Restores the original root directory contents when called.

        """
        self.elements = self.root_elements
        self.walker  = urwid.SimpleListWalker(self.root_elements)
        self.listbox = urwid.ListBox(self.walker)

        urwid.connect_signal(self.walker, 'modified', self.update)

        self.view.set_header(urwid.AttrWrap(urwid.Columns([
            urwid.Text('/', align='left'),
            urwid.Text('%s item(s)' % (len(self.root_elements)), align='right')
        ]), 'head'))

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
            for directory in sorted(trees):
                #element = ItemWidget(i, directory + '/')
                element = ItemWidget(i, directory.split('/')[-1] + '/') # We're just interested in the last subdir. And just append / to it.
                self.elements.append(element)
                i = i+1

        i = 0
        if not leaves:
            self.elements.append(ItemWidget(0, '../'))
        else:
            for k, v in sorted(leaves.iteritems()):
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

        # Set the header to the current directory so the user knows where they are. Also display how many items are there.
        self.view.set_header(urwid.AttrWrap(urwid.Columns([
            urwid.Text(str(self.focus), align='left'),
            urwid.Text('%s item(s)' % (len(leaves)), align='right')
        ]), 'head'))

        # Finally, set the body.
        self.view.set_body(self.listbox)

    def handle_trees(self):
        self.view.set_body(urwid.Filler(urwid.Text('hi'), 'top'))

    def handle_file(self):
        self.temp = '/usr/bin/vim %s'
        if self.last_dir == '': # This means root.
            key        = '__root__/%s' % (self.focus)
            future_dir = '' # So we can restore the directory later on
        else:
            key = self.last_dir + self.focus
            future_dir = self.last_dir

        file_leaves = self.parser.return_leaves(self.data, key)
        if not file_leaves:
            raise AppError('Could not grab the file URL.')

        # Remove the file from the key
        _directory = key.split('/')[:-1]
        _directory = '/'.join([str(i) for i in _directory])

        # Construct a directory path
        file_directory  = '/tmp/%s/%s/%s/%s' % (self.user, self.repository, self.branch, _directory)

        # Create the directory if it doesn't exist
        if not os.path.isdir(file_directory):
            os.makedirs(file_directory)

        file_location = '/tmp/%s/%s/%s/%s' % (self.user, self.repository, self.branch, key)

        # Set the header so we inform the user we are doing something
        self.view.set_header(urwid.AttrWrap(urwid.Text('Opening %s...' % (file_location)), 'head'))

        # Query the API...
        result = self.parser._query_api(file_leaves['url'])

        # If there's no content in the result then we've got a problem here...
        if not 'content' in result:
            raise AppError('There is no content in the API response!')

        try:
            # Now we need to create this file in /tmp
            file_location = '/tmp/%s/%s/%s/%s' % (self.user, self.repository, self.branch, key)
            fp = open(file_location, 'w')

            # Check whether it's raw or base64 encoded and write accordingly.
            if result['encoding'] == 'base64':
                fp.write(base64.b64decode(result['content']))
            else:
                fp.write(result['content'])

            # Flush so subprocess.call doesn't bitch about it
            fp.flush()

            # Now that we're done close the file.
            fp.close()

        except (OSError, IOError) as e:
            print('Unable to create/write to temp file: %s', str(e))

        # And open it in the editor using the editor string provided by the user.
        #subprocess.call(self.temp % (file_location))
        subprocess.call(self.temp % (file_location), shell=True)

        # Redraw or it's messed up
        self.loop.draw_screen()

        # Restore the directory
        self.focus    = future_dir
        self.last_dir = self.focus

        # And now reset the body
        if self.last_dir == '':
            self.handle_root_directory()
        else:
            self.handle_directory()

if __name__ == '__main__':
    try:
        QGH()
    except KeyboardInterrupt:
        print('^C caught, exiting...')
    except ValueError as e:
        print('ValueError: ' + str(e))
    except AppError as e:
        print('qgh error: ' + str(e))
