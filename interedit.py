import sys,os
import string
import csv
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

GRAMMAR_DIR = "grammars"

class WordButton(QtGui.QPushButton):
	def __init__(self,word,id):
		super(WordButton, self).__init__()
		self.setText(word)
		self.original = word
		self.id = id

	def contextMenuEvent(self, event):
		menu = QtGui.QMenu(self)
		editAction = menu.addAction("&Edit word")

		action = menu.exec_(self.mapToGlobal(event.pos()))
		if action == editAction:
			text,ok = QtGui.QInputDialog.getText(self,self.text(),"New value:")
			if ok:
				self.setText(text)

class TransLineEdit(QtGui.QLineEdit):
	# Re implemented for the focus in/out events (to know if it is currently selected or not)

	keyDownPressed = QtCore.pyqtSignal()

	def __init__(self, parent = None):
		super(TransLineEdit, self).__init__(parent)
		self.active = False

	def event(self,event):
		if (event.type()==QtCore.QEvent.KeyPress) and (event.key()==Qt.Key_Down):
			self.keyDownPressed.emit()
			return True
		return QtGui.QLineEdit.event(self, event)

	def focusInEvent(self, e):
		self.active = True
		super(TransLineEdit, self).focusInEvent(e)

	def focusOutEvent(self, e):
		self.active = False
		super(TransLineEdit, self).focusOutEvent(e)

class GramLineEdit(QtGui.QLineEdit):
	def __init__(self,grammarDict=None,css=None, parent=None):
		super(GramLineEdit, self).__init__(parent)
		self.grammarDict = grammarDict
		self.setStyleSheet(css)
		self.initUI()

	def initUI(self):
		self.textChanged.connect(self.textChanged_)

	def textChanged_(self):
		grammarStr = ""

class OriginalWindow(QtGui.QWidget):
	def __init__(self, text, fontSize = 12, parent=None):
		super(OriginalWindow, self).__init__(parent)
		self.fontSize = fontSize
		self.text = text
		self.initialize()

	def initialize(self):
		# Make a scroll area and put a QLabel inside it
		self.scrollArea = QtGui.QScrollArea(self)
		self.scrollArea.setWidgetResizable(True)
		# Buttons for zoom
		self.zoomLayout = QtGui.QHBoxLayout()
		# The layout for our window
		layout = QtGui.QVBoxLayout(self)
		layout.addWidget(self.scrollArea)
		layout.setContentsMargins(0,0,0,0)

		self.chapterText = QtGui.QLabel(self.text)
		self.chapterText.setTextInteractionFlags(Qt.TextSelectableByMouse)
		self.chapterText.setContentsMargins(10,5,10,5)
		self.chapterText.setWordWrap(True)
		self.chapterText.setAlignment(Qt.AlignJustify)
		font = QtGui.QFont("",self.fontSize)
		self.chapterText.setFont(font)
		self.scrollArea.setWidget(self.chapterText)

	def keyPressEvent(self, event):
		if event.key() == QtCore.Qt.Key_Escape:
			self.hide()
			event.accept()
		elif event.key() == QtCore.Qt.Key_Plus:
			self.fontSize += 1
			font = QtGui.QFont("",self.fontSize)
			self.chapterText.setFont(font)
		elif event.key() == QtCore.Qt.Key_Minus:
			self.fontSize -= 1
			font = QtGui.QFont("",self.fontSize)
			self.chapterText.setFont(font)
		else:
			super(OriginalWindow, self).keyPressEvent(event)

class ErrorPopup(QtGui.QMessageBox):
	def __init__(self, title, msg, parent=None):
		super(ErrorPopup, self).__init__(parent)
		self.setIcon(QtGui.QMessageBox.Warning)
		self.setWindowTitle(title)
		self.setText(msg)

class GrammarWindow(QtGui.QDialog):
	def __init__(self, grammarDict, parent=None):
		super(GrammarWindow, self).__init__(parent)
		self.grammarDict = grammarDict
		self.originalKey = ""
		self.initUI()

	def initUI(self):
		widget = QtGui.QWidget()
		layout = QtGui.QVBoxLayout()
		layout.setAlignment(Qt.AlignTop)
		layout.setContentsMargins(2,2,2,2)
		# Where we type new grammar items
		self.grammarLineEdit = QtGui.QLineEdit()
		itemList = sorted(list(self.grammarDict))
		model = QtGui.QStringListModel()
		model.setStringList(itemList)
		self.completer = GrammarCompleter(self.grammarLineEdit)
		self.completer.setCompletionMode(QtGui.QCompleter.PopupCompletion)
		self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
		self.completer.setModel(model)
		self.grammarLineEdit.setCompleter(self.completer)
		self.grammarLineEdit.textChanged.connect(self.textChanged)

		downAction = QtGui.QAction(self.grammarLineEdit)
		downAction.setShortcut("Down")
		downAction.triggered.connect(self.completer.complete)
		self.grammarLineEdit.addAction(downAction)

		# Where we type the grammar pop up information
		self.grammarTextEdit = QtGui.QTextEdit()
		# The submit buttons
		buttonWidget = QtGui.QWidget()
		buttonLayout = QtGui.QHBoxLayout(buttonWidget)
		buttonLayout.setContentsMargins(0,0,0,0)
		self.button = QtGui.QPushButton("Add")
		self.button.clicked.connect(self.addGrammar)
		self.button.setMaximumWidth(40)
		self.saveButton = QtGui.QPushButton("Save")
		self.saveButton.clicked.connect(self.addGrammar)
		self.saveButton.setMaximumWidth(40)
		self.saveButton.setVisible(False)
		buttonLayout.addWidget(self.button)
		buttonLayout.addWidget(self.saveButton)
		# Add all the widgets to layout
		layout.addWidget(self.grammarLineEdit)
		layout.addWidget(self.grammarTextEdit)
		layout.addWidget(buttonWidget)

		self.setLayout(layout)
		self.setWindowTitle("Edit Grammar")

	def addGrammar(self):
		if self.button.text() == "Edit" and not self.saveButton.isVisible():
			self.originalKey = self.grammarLineEdit.displayText()
			self.button.setEnabled(False)
			self.saveButton.setVisible(True)
			self.grammarTextEdit.setEnabled(True)
		else:
			# if save was pressed and not add
			if self.saveButton.isVisible():
				del self.grammarDict[self.originalKey]
				self.button.setEnabled(True)
				self.saveButton.setVisible(False)
			key = self.grammarLineEdit.text()
			val = self.grammarTextEdit.toPlainText()
			# Add to dictionary
			self.grammarDict[key] = val
			# Reset fields
			self.grammarLineEdit.setText("")
			self.grammarLineEdit.setFocus()
			self.grammarTextEdit.setText("")
			# Update completer data
			self.completer = QtGui.QCompleter(sorted(list(self.grammarDict)), self.grammarLineEdit)
			self.grammarLineEdit.setCompleter(self.completer)
			self.grammarLineEdit.completer().complete()

	def textChanged(self):
		if not self.saveButton.isVisible():
			key = self.grammarLineEdit.text()
			if key in self.grammarDict:
				self.button.setText("Edit")
				self.grammarTextEdit.setText(self.grammarDict[key])
				self.grammarTextEdit.setEnabled(False)
			else:
				self.button.setText("Add")
				self.grammarTextEdit.setText("")
				self.grammarTextEdit.setEnabled(True)

class GrammarCompleter(QtGui.QCompleter):
	def __init__(self, parent=None):
		super(GrammarCompleter, self).__init__(parent)

	def setModel(self, model):
		self.sourceModel = model
		self.filterProxyModel = QtGui.QSortFilterProxyModel(self)
		self.filterProxyModel.setSourceModel(self.sourceModel)
		super(GrammarCompleter, self).setModel(self.filterProxyModel)

	def updateModel(self):
		# Let / autocomplete until the next / using regexp
		pattern = QtCore.QRegExp(self.completionPrefix.replace("/",".*/"), QtCore.Qt.CaseInsensitive, QtCore.QRegExp.RegExp)
		self.filterProxyModel.setFilterRegExp(pattern)

	def splitPath(self, path):
		# path = user's input
		self.completionPrefix = path
		self.updateModel()
		return ""

class Main(QtGui.QMainWindow):
	def __init__(self, parent = None):
		QtGui.QMainWindow.__init__(self,parent)

		self.filename = ""
		self.saved = False
		self.loaded = False
		self.language = ""
		self.originalFontSize = 12
		self.languageList = self.initGrammar()
		self.grammarDict = {}
		self.initUI()

	def initGrammar(self):
		languages = []
		if os.path.isdir(GRAMMAR_DIR):
			for language in os.listdir(GRAMMAR_DIR):
				if language.endswith(".ilg"):
					languages.append(language.rstrip('.ilg'))
			languages.sort()
		else:
			msg = "Can't find 'grammars' directory!\n\nPlease make sure you've downloaded the latest files from the repository."
			title = "No language data"
			errorMsg = ErrorPopup(title,msg)
			answer = errorMsg.exec_()
		return languages

	def initUI(self):
		# Initialize
		self.initToolbar()
		self.initMenubar()
		self.initCentral()

		# Initialize a statusbar for the window
		self.statusbar = self.statusBar()

		# Read settings file and load previously opened file
		settingsFile = "settings.cfg"
		if os.path.isfile(settingsFile):
			with open(settingsFile,"rt") as file:
				filename = file.read()
				self.open(filename)

	def initCentral(self):
		# Everything will go in this central widget
		self.centralWidget = QtGui.QWidget()
		# Put the scroll area into a VBox layout
		layout = QtGui.QVBoxLayout(self.centralWidget)
		self.scrollArea = QtGui.QScrollArea(self.centralWidget)
		self.scrollArea.setWidgetResizable(True)
		# the chapter combo box goes here
		self.chapterBox = QtGui.QHBoxLayout()
		# add the combo box layout and the text layout
		layout.addLayout(self.chapterBox)
		layout.addWidget(self.scrollArea)

		layout.setSpacing(0)

		layout.setContentsMargins(0,0,0,0)

		# Add a widget into the scroll area where our contents will go
		self.scrollAreaStack = QtGui.QStackedWidget()
		self.scrollArea.setWidget(self.scrollAreaStack)

		self.setCentralWidget(self.centralWidget)

		# x and y coordinates on the screen, width, height
		self.setGeometry(100,100,1030,800)
		self.setWindowTitle("InterLinear Editor")

	def initToolbar(self):
		# New button
		self.newAction = QtGui.QAction(QtGui.QIcon("icons/new.png"),"New",self)
		self.newAction.setStatusTip("Start a new project")
		self.newAction.setShortcut("Ctrl+N")
		self.newAction.triggered.connect(self.new)
		# Open button
		self.openAction = QtGui.QAction(QtGui.QIcon("icons/open.png"),"Open",self)
		self.openAction.setStatusTip("Open project")
		self.openAction.setShortcut("Ctrl+O")
		self.openAction.triggered.connect(self.open)
		# Save button
		self.saveAction = QtGui.QAction(QtGui.QIcon("icons/save.png"),"Save",self)
		self.saveAction.setStatusTip("Save project")
		self.saveAction.setShortcut("Ctrl+S")
		self.saveAction.triggered.connect(self.save)
		# Export button
		self.exportAction = QtGui.QAction(QtGui.QIcon("icons/export.png"),"Export",self)
		self.exportAction.setStatusTip("Export project")
		self.exportAction.setShortcut("Ctrl+E")
		self.exportAction.triggered.connect(self.export)
		# Multi-word button
		self.multiAction = QtGui.QAction(QtGui.QIcon("icons/multi.png"),"Multi-Word",self)
		self.multiAction.setStatusTip("Add multi-word translation")
		self.multiAction.setShortcut("Ctrl+M")
		self.multiAction.triggered.connect(self.multiAdd)
		# Remove multi-word button
		self.multiRemAction = QtGui.QAction(QtGui.QIcon("icons/multiRemove.png"),"Remove Multi-Word",self)
		self.multiRemAction.setStatusTip("Remove multi-word translation")
		self.multiRemAction.setShortcut("Ctrl+Shift+M")
		self.multiRemAction.triggered.connect(self.multiRemove)
		# Show original text
		self.showTextAction = QtGui.QAction(QtGui.QIcon("icons/original.png"),"Show original",self)
		self.showTextAction.setStatusTip("Show original text in a pop-up window")
		self.showTextAction.setShortcut("Ctrl+T")
		self.showTextAction.triggered.connect(self.showText)

		# Create toolbar
		self.toolbar = self.addToolBar("Options")

		# Add our actions to toolbar
		self.toolbar.addAction(self.newAction)
		self.toolbar.addAction(self.openAction)
		self.toolbar.addAction(self.saveAction)
		self.toolbar.addAction(self.exportAction)
		self.toolbar.addSeparator()
		self.toolbar.addAction(self.multiAction)
		self.toolbar.addAction(self.multiRemAction)
		self.toolbar.addSeparator()
		self.toolbar.addAction(self.showTextAction)

	def initMenubar(self):
		self.menubar = self.menuBar()

		# Create an exit action
		self.exitAction = QtGui.QAction("Exit",self)
		self.exitAction.setStatusTip("Exit program")
		self.exitAction.setShortcut("Ctrl+Q")
		self.exitAction.triggered.connect(QtGui.qApp.quit)
		# Create a save as action
		self.saveAsAction = QtGui.QAction("Save As",self)
		self.saveAsAction.setStatusTip("Save project as")
		self.saveAsAction.setShortcut("Ctrl+Shift+S")
		self.saveAsAction.triggered.connect(self.saveAs)

		# File
		fileMenu = self.menubar.addMenu("&File")
		fileMenu.addAction(self.newAction)
		fileMenu.addAction(self.openAction)
		fileMenu.addAction(self.saveAction)
		fileMenu.addAction(self.saveAsAction)
		fileMenu.addAction(self.exportAction)
		fileMenu.addAction(self.exitAction)
		# Edit
		editMenu = self.menubar.addMenu("&Edit")
		# Grammar
		self.grammarMenu = self.menubar.addMenu("&Grammar")
		self.setLanguageMenu = self.grammarMenu.addMenu("Set Language")
		self.languageGroup = QtGui.QActionGroup(self.setLanguageMenu)
		for language in self.languageList:
			# Add action to actionGroup
			action = self.languageGroup.addAction(language.capitalize())
			action.setCheckable(True)
			action.triggered[()].connect(lambda language=language: self.changeLanguage(language))
			# Add action to menu
			self.setLanguageMenu.addAction(action)
		self.grammarAction = self.grammarMenu.addAction("Add/Edit &Grammar",self.addGrammar)
		self.grammarAction.setShortcut("Ctrl+G")
		# Tools
		toolMenu = self.menubar.addMenu("&Tools")
		toolMenu.addAction(self.multiAction)
		toolMenu.addAction(self.multiRemAction)

	# ACTIONS #

	def new(self):
		filename = QtGui.QFileDialog.getOpenFileName(self, 'Load Text',".","(*.txt);;All(*.*)")

		# Open file
		if filename:
			with open(filename,"rt") as file:
				self.text = Text(file.read().rstrip())
			self.buildChapters()
		# clear out any previous filename
		self.filename = ""

	def buildChapters(self):
		self.initCentral()
		# build chapter list
		self.chapterListMenu = QtGui.QComboBox()
		self.chapterListMenu.setMaximumWidth(120)
		self.chapterListMenu.currentIndexChanged.connect(self.changeChapter)
		self.chapterListMenu.addItems(["Chapter {}".format(x+1) for x in range(self.text.numChapters)])
		hbox = QtGui.QVBoxLayout()
		hbox.addWidget(self.chapterListMenu)
		self.chapterBox.addLayout(hbox)

		self.scrollAreaList = []
		for i in range(self.text.numChapters):
			self.scrollAreaList.append(QtGui.QWidget())
			self.scrollAreaStack.addWidget(self.scrollAreaList[i])
		# First change chapter to 1, otherwise changeChapter won't let us change
		self.text.currentChapter = 1
		self.changeChapter(0)

	def open(self,filename=""):
		if filename:
			self.filename = filename
		else:
			self.filename = QtGui.QFileDialog.getOpenFileName(self, 'Open File',".","(*.ilt)")

		# If we succeeded, open and read file
		if self.filename:
			# Store the file in the settings file to automatically load it next time
			with open("settings.cfg","wt") as file:
				file.write(self.filename)
			with open(self.filename,"rt") as file:
				fileContents = file.read()
				# First load the language if any of the file
				if "<<<LANG:" in fileContents:
					self.language = pullString(fileContents,"<<<LANG:",">>>")
					if self.language:
						filename = GRAMMAR_DIR+"/"+self.language+".ilg"
						with open(filename,"rt") as f:
							reader = csv.reader(f,delimiter=":")
							self.grammarDict = dict(reader)
				# Load language grammar rules
				self.changeLanguage(self.language)
				# Check the language in the [Grammar->Languages] menu
				for action in self.languageGroup.findChildren(QtGui.QAction):
					if action.text().lower() == self.language:
						action.setChecked(True)
				# Count number of chapters in book
				numChapters = fileContents.count("<<<CHAPTER>>>")
				# divide the text into chapters
				chapters = fileContents.split("<<<CHAPTER>>>\n\n")
				original = ""
				translation = ""
				grammar = ""
				for i in range(1,numChapters+1):
					(orig,trans_gram) = chapters[i].split("\n\n<<<TRAN>>>\n\n")
					original += "\n_DIV_\n\n" + orig.strip()
					(trans,gram) = trans_gram.split("<<<GRAM>>>\n")
					translation += "\n_DIV_\n\n" + trans.strip()
					grammar += "\n_DIV_\n\n" + gram.strip()
				# create the text object
				self.text = Text(original,translation,grammar)
				self.buildChapters()
				self.saved = True

	def save(self):
		if self.loaded:
			# If we haven't saved yet, give it a name
			if not self.filename:
				self.filename = QtGui.QFileDialog.getSaveFileName(self, "Save File",".","(*.ilt)")

			# If we selected a file, save. Otherwise, do nothing.
			if self.filename:
				# make sure the original text is up to date
				self.buildOriginal()
				# Make sure file ends with our .ilt extension
				if not self.filename.endswith(".ilt"):
					self.filename += ".ilt"

				# Now that we have a name, save

				with open(self.filename,"w") as file:
					string = "<<<LANG:{}>>>\n".format(self.language)
					i = 0
					curRow = 0
					for chapter in self.text.chapterList:
						original = "\n<<<CHAPTER>>>\n\n"+chapter+"\n\n"
						translation = "<<<TRAN>>>\n\n"
						grammar = "<<<GRAM>>>\n\n"
						if self.text.wordList[i]:
							for (row,org,trans,gram) in self.text.wordList[i]:
								translation += "= " + trans.text() + " "
								grammar += "= " + gram.text() + " "
						else:
							translation += self.text.translationList[i].strip()+" "
							grammar += self.text.grammarList[i].strip()+" "
						string += original + translation[:-1] + "\n\n" + grammar[:-1] + "\n"
						i += 1
					file.write(string)
					self.saved = True
			# If a language is set, save language data
			if self.language:
				filename = GRAMMAR_DIR+"/"+self.language+".ilg"
				with open(filename,"wt") as f:
					writer = csv.writer(f,delimiter=":")
					for key,value in self.grammarDict.items():
						writer.writerow([key,value])

	def saveAs(self):
		if self.loaded:
			filename = self.filename
			self.filename = ""
			self.save()
			# If it was cancelled, reset the filename to the old name
			if not self.filename:
				self.filename = filename

	def export(self):
		if self.loaded:
			if self.filename:
				self.save()
				self.buildOriginal()
				with open(self.filename+"x","wt") as f:
					fileText = ""
					for i in range(self.text.numChapters):
						# Build string from our entered data
						fileText += "<<<PAGE>>>\n\n" + self.text.chapterList[i] + "\n\n"
						original = "<<<ORG>>>\n"
						translation = "<<<TRAN>>>\n"
						if self.text.wordList[i]:
							for (row,org,trans,gram) in self.text.wordList[i]:
								original += "= " + org.text().strip(' ,.!?/-_;\n') + " "
								translation += "= " + trans.text() + " "
						else:
							translation += self.text.translationList[i].strip()+" "
						fileText += original[:-1] + "\n"
						fileText += translation[:-1] + "\n\n"
					f.write(fileText)
			else:
				# prompt user to save
				savedMsg = QtGui.QMessageBox()
				savedMsg.setIcon(QtGui.QMessageBox.Warning)
				savedMsg.setText("You must save before exporting!\nSave now?")
				savedMsg.setWindowTitle("Save?")
				savedMsg.setStandardButtons(QtGui.QMessageBox.No | QtGui.QMessageBox.Yes )
				answer = savedMsg.exec_()
				if answer == QtGui.QMessageBox.Yes:
					self.save()

	def multiAdd(self):
		if self.loaded:
			curChap = self.text.currentChapter
			selectedWords = []
			numWords = 0
			# Find which words have been selected
			for (rows,orig,trans,gram) in self.text.wordList[curChap]:
				if orig.isChecked():
					numWords += 1
					selectedWords.append((orig,trans))
			# Make sure we've selected something, first
			if numWords > 0:

				words = "["
				defaultText = ""
				for (orig,trans) in selectedWords:
					words += orig.text()+", "
					defaultText += orig.text() + " "
				words = words[:-2]+"]"
				defaultText = defaultText[:-1] + "; "

				text,ok = QtGui.QInputDialog.getText(self, words, "Enter translation:", text = defaultText)
				if ok:
					for (orig,trans) in selectedWords:
						trans.setText(trans.text().rstrip()+" ["+text+"]")
						orig.setChecked(False)

	def multiRemove(self):
		if self.loaded:
			curChap = self.text.currentChapter
			# Find which words have been selected
			for (rows,orig,trans,gram) in self.text.wordList[curChap]:
				if orig.isChecked():
					orig.setChecked(False)
					if '[' in trans.text() and ']' in trans.text():
						text = trans.text()
						trans.setText(text[:text.rfind('[')].rstrip())

	def showText(self):
		if self.loaded:
			# Make sure the original text is up to date
			self.buildOriginal()

			curChap = self.text.currentChapter
			# Grab the text from the current chapter
			text = self.text.chapterList[curChap].replace('\n','\n\n')
			# Give new lines a special character to be treated as punctuation
			words = text.replace('\n\n','# ').split(' ')
			i = 0
			isSelection = False
			# Find the currently selected input box (where the text cursor is)
			for (row,org,trans,gram) in self.text.wordList[curChap]:
				if trans.active == True:
					isSelection = True
					break
				i += 1
			# If the cursor is in a box, bold the sentence it's in
			if isSelection:
				punctuation = ['.','!','?','#']
				iL = i-1
				iR = i
				while words[iL][-1] not in punctuation:
					iL -= 1
				while words[iR][-1] not in punctuation:
					iR += 1
				words[iR] = words[iR].rstrip('#')

				sentence = ""
				for i in range(iL+1,iR+1):
					sentence += words[i] + " "
				sentence = sentence[:-1]
				text = text.replace(sentence,"<B>"+sentence+"</B>").replace("\n\n","<BR><BR>")

			# The window will go into this widget
			self.textWindow = OriginalWindow(text)
			self.textWindow.setWindowTitle("Chapter {}".format(curChap+1))

			self.textWindow.show()

	def changeLanguage(self, language):
		if language:
			self.language = language
			filename = GRAMMAR_DIR+"/"+language+".ilg"
			# make sure grammars directory exists
			if os.path.isdir(GRAMMAR_DIR):
				with open(filename,"rt") as f:
					grammar = f.read()

	def addGrammar(self):
		# create and execute QDialog
		self.window = GrammarWindow(self.grammarDict)
		self.window.exec_()
		# save the new dictionary
		self.grammarDict = self.window.grammarDict
		for row,orig,trans,gram in self.text.wordList[self.text.currentChapter]:
			itemList = sorted(list(self.grammarDict))
			model = QtGui.QStringListModel()
			model.setStringList(itemList)
			gram.completer().setModel(model)

	# MISC ROUTINES #
	"""	loadText
		*chapter = chapter number to load (starts at 0)
		*original = the untranslated text
		translation (optional) = the already translated text
		grammar (optional) = list of grammar notes
	"""
	def loadText(self, chapter, original, translation="", grammar=""):
		# build translation list if we've already got a translation
		if translation:
			translation = translation.split("=")
			del translation[0]

		if grammar:
			grammar = grammar.split("=")
			del grammar[0]

		# split paragraphs
		paragraphsOriginal = original.split('\n')

		wordList = []
		wordCount = 0
		rows = -1
		# Each word is placed in a vbox with the original and translation
		vbox = QtGui.QVBoxLayout()
		vbox.setAlignment(Qt.AlignTop)
		for paragraph in paragraphsOriginal:
			rows += 1
			# Split the text into words
			words = paragraph.split(' ')
			# Character counter
			chars = 0
			for word in words:
				# Check if character goes past end of screen
				chars += len(word)
				if chars > 60:
					chars = 0
					rows += 1
				# Create [original] button
				orig = WordButton(word,wordCount)
				orig.setCheckable(True)
				orig.setFlat(True)
				orig.setStyleSheet("""	QPushButton {
											background: none;
											border: none;
											text-align: left;
											padding: 0px 1px;
											margin: 0 0px;
										}
										QPushButton:pressed {
											background:#DCDCDC;
											border: 1px solid #A5A5E5;
										}
										QPushButton:checked {
											background:#DCDCDC;
											border: 1px solid #A5A5E5;
										}""")
				orig.setFocusPolicy(Qt.NoFocus)
				if translation and len(translation) > wordCount:
					trans = TransLineEdit(translation[wordCount].strip())
				else:
					trans = TransLineEdit()
				trans.home(True)
				# Special signal to move cursor down
				trans.keyDownPressed.connect(self.keyDownPressed)
				css = "text-align: left; padding: 0px 1px; margin: 0 0px; border: 1px dotted darkgray; background: white;"
				trans.setStyleSheet(css)
				# set up grammar box and special grammar completer
				if grammar and len(grammar) > wordCount:
					gram = QtGui.QLineEdit(grammar[wordCount].strip())
				else:
					gram = QtGui.QLineEdit()
				gram.setStyleSheet(css)
				itemList = sorted(list(self.grammarDict))
				model = QtGui.QStringListModel()
				model.setStringList(itemList)
				self.completer = GrammarCompleter(gram)
				self.completer.setCompletionMode(QtGui.QCompleter.PopupCompletion)
				self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
				self.completer.setModel(model)
				gram.setCompleter(self.completer)

				#gram.setStyleSheet(css)
				gram.setFocusPolicy(Qt.ClickFocus)

				# Add original/translation to wordList
				wordList.append([rows,orig,trans,gram])
				wordCount += 1
		# Make a list with each row of the text
		hboxList = []
		for i in range(rows+1):
			hboxList.append(QtGui.QHBoxLayout())
		# Populate list
		# wordBox is a vbox layout which goes inside the hboxList to form a line of text
		for (row,org,trans,gram) in wordList:
			wordBox = QtGui.QVBoxLayout()
			wordBox.addWidget(org)
			wordBox.addWidget(trans)
			wordBox.addWidget(gram)
			hboxList[row].addLayout(wordBox)
			hboxList[row].setContentsMargins(0,0,0,0)
			hboxList[row].setSpacing(0)
			hboxList[row].setAlignment(Qt.AlignLeft)

		# add it to the proper chapter's wordlist
		self.text.wordList[chapter] = wordList

		# add all lines to the main vbox layout
		for i in range(len(hboxList)):
			hboxList[i].addStretch(1)
			vbox.addLayout(hboxList[i])
		self.scrollAreaList[chapter].setLayout(vbox)
		self.loaded = True

	def changeChapter(self,i):
		if(i != self.text.currentChapter):
			if not self.scrollAreaList[i].layout():
				translation = grammar = ""
				if self.text.translationList[i]:
					translation = self.text.translationList[i]
				if self.text.grammarList[i]:
					grammar = self.text.grammarList[i]
				self.loadText(i,self.text.chapterList[i],translation,grammar)
			self.text.currentChapter = i
			self.scrollAreaStack.setCurrentIndex(i)

	def buildOriginal(self):
		i = 0
		for chapter in self.text.chapterList:
			# check if we've loaded that text
			if self.text.wordList[i]:
				paragraphs = chapter.split('\n')
				chapterWords = []
				# Split into paragraphs and add a \n to last word
				for paragraph in paragraphs:
					chapterWords += paragraph.split(' ')
					chapterWords[-1] += '\n'
				chapterWords[-1] = chapterWords[-1][:-1]
				chapter = ""
				j = 0
				for word in chapterWords:
					wordList = self.text.wordList[i][j]
					row, org, trans, gram = wordList
					if "\n" not in word:
						word += " "
					word = word.replace(org.original,org.text())
					chapter += word
					j += 1
				self.text.chapterList[i] = chapter[:-1]
			i += 1

	def keyDownPressed(self):
		# Find the currently selected input box (where the text cursor is)
		# ..and set the focus to the grammar box underneath
		for (row,org,trans,gram) in self.text.wordList[self.text.currentChapter]:
			if trans.active == True:
				gram.setFocus(True)

def pullString(str,delim1,delim2):
	strStart = str.find(delim1) + len(delim1)
	if delim2 != -1:
		strEnd = str.find(delim2)
		return str[strStart:strEnd]
	else:
		return str[strStart:]

"""	This class handles our text
	Variables
	---------
	original:
		original unformatted text
	translation
	grammar
	wordList
	currentChapter
	numChapters
	chapterList
"""
class Text:
	def __init__(self,original,translation="",grammar=""):
		self.original = original
		# This holds a list of widgets for each chapter: row,original,translation,grammar
		self.wordList = []
		self.currentChapter = 0
		# count chapters and split text into chapters
		self.numChapters = self.original.count("_DIV_")
		self.chapterList = self.original.split("_DIV_")

		# first entry should be an empty string
		del self.chapterList[0]

		# Build empty set if we need it
		emptyList = []
		for i in range(self.numChapters):
			paragraphs = self.chapterList[i].split('\n')
			empty = ""
			for paragraph in paragraphs:
				words = paragraph.split(' ')
				for word in words:
					empty += "= "
			emptyList.append(empty)

		# translation per chapter
		self.translationList = ['']*self.numChapters
		if translation:
			self.translationList = translation.split("_DIV_")
			del self.translationList[0]
		else:
			# build empty translation list based on number of words in text
			self.translationList = emptyList

		# grammar section per chapter
		self.grammarList = ['']*self.numChapters
		if grammar:
			self.grammarList = grammar.split("_DIV_")
			del self.grammarList[0]
		else:
			# build empty translation list based on number of words in text
			self.grammarList = emptyList

		# create empty wordlist for each chapter
		for i in range(self.numChapters):
			self.wordList.append([])

		# remove extra whitespace
		for i in range(len(self.chapterList)):
			self.chapterList[i] = self.chapterList[i].replace("\n\n","\n")
			self.chapterList[i] = self.chapterList[i].strip()

def main():

	app = QtGui.QApplication(sys.argv)

	main = Main()
	main.show()

	sys.exit(app.exec_())

if __name__ == "__main__":
	main()
