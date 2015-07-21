### qgh
Console curses browser for github repo contents.

![Screenshot](https://raw.githubusercontent.com/infyhr/qgh/master/screenshot.png "Screenshot")

### requirements
* httplib
* urwid
* python2.7

### features
* Display all files and directories from a given repository and browse through them in a curses TUI
* Branch support
* Open files in user set editor (vim, for example)

#### todo
* Count entries in tree
* logger

#### maybe sometime in future
* List separately files and dirs
* Regex search through said
* Themes (colors? :smile:)
* Issues
* Repository information (stats, users...)
* emoji support for icons
* guess file type
* ...whatever

### installation
First, it is recommended you create a Python [virtualenv](https://virtualenv.pypa.io/en/latest/index.html) (`virtualenv env && source env/bin/activate`) to avoid installing dependencies on a system-wide level.

Next, run `pip install -r requirements.txt` to install the necessary dependencies.

To use qgh, run `python qgh/qgh.py user/repository [branch]`.

Example given: `python qgh/qgh.py infyhr/qgh`. `master` is always the default branch and can be ommited then.

If your terminal doesn't redraw properly after using `vim` then `^L` to force a redraw.