# InterText
A simple tool for creating and translating interlinear texts, using Python 3 and PyQt4.

## Getting started
A few tips before you get started.

### What you will need
You'll need to have Python 3 installed as well as PyQt4.

**Windows:**

1. Download and install the latest Python 3 version from https://www.python.org/downloads/
2. Scroll down to the "Binary Packages" section and download and install the latest PyQt4 from https://www.riverbankcomputing.com/software/pyqt/download
3. Download and extract the InterText repository. You should be able to double-click intertext.py to open the program.

**Linux:**

1. User your package manager to install PyQt4 and Python 3. For example, under Fedora: `sudo dnf install python3 PyQt4`
2. Download the InterText repository. Run `python3 interedit.py` from the terminal.

### New
Load a new .txt file with chapters separated by _DIV_ (including a _DIV_ at the top of the .txt file before the first chapter). If your .txt file has 10 chapters, there should be 10 _DIV_s.

### Open
Open an existing project. Saved projects should have the .ilt extension.

### Export
Export a project into the format required by the learn-to-read-foreign-languages.com interlinear text scripts.

## Notes
Currently the second row of text input boxes doesn't do anything (and isn't saved). Later it will be used for grammar explanations.

