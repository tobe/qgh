### qgh
Console curses browser for github repo contents.

![Screenshot](https://raw.githubusercontent.com/infyhr/qgh/master/screenshot.png "Screenshot")

### requirements
* httplib
* urwid
* python2.7

### features
* Display all files and directories from a given repository and browse through them in a curses-like TUI.

### installation
First, it is recommended you create a Python [virtualenv](https://virtualenv.pypa.io/en/latest/index.html) (`virtualenv env && source env/bin/activate`) to avoid installing dependencies on a system-wide level.

Next, run `pip install -r requirements.txt` to install the necessary dependencies.

To use qgh, run `python qgh/qgh.py user/repository [branch]`.
Example given: `python qgh/qgh.py infyhr/qgh`. `master` is always the default branch and can be ommited then.
