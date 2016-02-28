#!/usr/bin/python
# -*- coding: utf-8 -*-

# Main handler?

import urwid
import os
import base64
import subprocess

class FileHandler:
    def __init__(self, qgh):
        self.QGH = qgh;

    def handle_file(self):
        if self.QGH.last_dir == '': # This means root.
            key        = '__root__/%s' % (self.QGH.focus)
            future_dir = '' # So we can restore the directory later on
        else:
            key = self.QGH.last_dir + self.QGH.focus
            future_dir = self.QGH.last_dir

        file_leaves = self.QGH.Parser.return_leaves(self.QGH.data, key)
        if not file_leaves:
            raise AppError('Could not grab the file URL.')

        # Remove the file from the key
        _directory = key.split('/')[:-1]
        _directory = '/'.join([str(i) for i in _directory])

        # Construct a directory path
        file_directory  = '/tmp/%s/%s/%s/%s' % (self.QGH.user, self.QGH.repository, self.QGH.branch, _directory)

        # Create the directory if it doesn't exist
        if not os.path.isdir(file_directory):
            os.makedirs(file_directory)

        file_location = '/tmp/%s/%s/%s/%s' % (self.QGH.user, self.QGH.repository, self.QGH.branch, key)

        # Set the header so we inform the user we are doing something
        self.QGH.view.set_header(urwid.AttrWrap(urwid.Text('Opening %s...' % (file_location)), 'head'))

        # Query the API...
        result = self.QGH.Parser._query_api(file_leaves['url'])

        # If there's no content in the result then we've got a problem here...
        if not 'content' in result:
            raise AppError('There is no content in the API response!')

        try:
            # Now we need to create this file in /tmp
            file_location = '/tmp/%s/%s/%s/%s' % (self.QGH.user, self.QGH.repository, self.QGH.branch, key)
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
        #subprocess.call(self.config.data['editor'] % (file_location), shell=True)
        subprocess.call(self.QGH.Config.get_editor % (file_location), shell=True)

        # Redraw or it's messed up
        self.QGH.loop.draw_screen()

        # Restore the directory
        self.QGH.focus    = future_dir
        self.QGH.last_dir = self.QGH.focus

        # And now reset the body
        if self.QGH.last_dir == '':
            self.QGH.MainHandler.handle_root_directory()
        else:
            self.QGH.MainHandler.handle_directory()