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
            #('fixed', 4, urwid.Padding(urwid.AttrWrap(urwid.Text(self.identifier), self.color, 'focus'), left=2)),
            ('fixed', 4, urwid.Padding(urwid.Text(self.identifier), left=2)),
            #(10, urwid.AttrWrap(urwid.Text('%s' % self.size), self.color, 'focus')),
            (10, urwid.Text('%s' % self.size)),
            #urwid.AttrWrap(urwid.Text('%s' % url.split('/')[-1]), self.color, 'focus')
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

class MainHandler():
    """ add doc here """
    def __init__(self): pass

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
            for k, v in sorted(leaves.items()):
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
            fp = open(file_location, 'wb')

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
            print(('Unable to create/write to temp file: %s', str(e)))

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
