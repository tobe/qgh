### qgh
Console curses browser for github repo contents.

![Screenshot](https://raw.githubusercontent.com/infyhr/qgh/master/screenshot.png "Screenshot")

### requirements
* urwid 1.3.0
* python3.4

### features
* Display all files and directories from a given repository and browse through them in a curses TUI
* Branch support
* Open files in your favorite editor.
* Regex lazy search
* Some basic vi binds

### todo & maybe sometime in future...
moved [over here](https://github.com/infyhr/qgh/issues?utf8=%E2%9C%93&q=is%3Aopen+is%3Aissue+label%3Aenhancement) :eyes:

### installation
First, it is recommended you create a Python [virtualenv](https://virtualenv.pypa.io/en/latest/index.html) (`virtualenv env && source env/bin/activate`) to avoid installing dependencies on a system-wide level.  

Next, run `pip install -r requirements.txt` to install the necessary dependencies.  

To use qgh, run `python qgh/qgh.py user/repository [branch]`.  

Example given: `python qgh/qgh.py infyhr/qgh`.  
`master` is always the default branch and can be ommited then.  

**Note:** If your terminal doesn't redraw properly after using `vim` then `^L` to force a redraw.
