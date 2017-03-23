import tkinter
import re
import sys

class AppUI(tkinter.Tk):
	def __init__(self, thisAppController, loop, interval = 0.01):
		super().__init__()
		self.protocol("WM_DELETE_WINDOW", self.close)
		self.width = 300
		self.height = 200
		self.currentGroupID = None
		self.geometry('{}x{}'.format(self.width,self.height))
		self.loop = loop
		self.tasks = []
		self.currentGroupIDWindow = None
		self.thisAppController = thisAppController
		self.updater(interval)
		
	async def startUI(self):
		# Code to add widgets will go here...
		self.title("Main Menu")
		self.mainMenuWindow = tkinter.Frame(self, width=self.width, height=self.height)
		self.mainMenuWindow.pack()
		startMainFunctionButton = tkinter.Button (self.mainMenuWindow, text = "Start Game Watcher", command = self.getGroupID).pack(fill = "x")
		createHeroReferenceImagesButton = tkinter.Button (self.mainMenuWindow, text = "Hero Reference: Create Images").pack(fill = "x")
		createHeroReferencesButton = tkinter.Button (self.mainMenuWindow, text = "Hero Reference: Create TXT").pack(fill = "x")
		createMapReferenceImagesButton = tkinter.Button (self.mainMenuWindow, text = "Map Reference: Create Images").pack(fill = "x")
		createMapReferencesButton = tkinter.Button (self.mainMenuWindow, text = "Map Reference: Create TXT").pack(fill = "x")
	
	def getGroupID(self):
		self.mainMenuWindow.destroy()
		groupIDWindow = tkinter.Frame(self, width=self.width, height=self.height)
		groupIDWindow.pack(side="top")
		self.title("Group ID Input")
		groupIDLabel = tkinter.Label(groupIDWindow, text = "Group ID")
		groupIDLabel.pack(side="left")
		groupIDEntry = tkinter.Entry(groupIDWindow, width = 20)
		groupIDEntry.pack(side="left")
		submitGroupID = tkinter.Button(groupIDWindow, text = "Submit", command = lambda: self.checkGroupID(groupIDEntry))
		submitGroupID.pack(side="left")
		errorWindow = tkinter.Frame(self)
		errorWindow.pack(side="top")
		self.errorMessageLabel = tkinter.Label(errorWindow, text = "", fg="red")
		self.errorMessageLabel.pack()
		
	def checkGroupID(self, entry):
		entryText = entry.get()
		entryText = entryText.lower().strip()
		if (entryText == self.currentGroupID):
			self.errorMessageLabel["text"] = "You are already in this room"
		elif (len(entryText) < 5):
			self.errorMessageLabel["text"] = "ID is too short"
		elif (len(entryText) > 5):
			self.errorMessageLabel["text"] = "ID is too long"
		elif (re.search('[a-z0-9]{5}', entryText)):
			for task in self.tasks:
				task.cancel()
				self.thisAppController.unsubscribeFromCurrent()
			self.tasks = []
			self.currentGroupID = entryText
			self.errorMessageLabel["text"] = ""
			self.inGameUI(entryText)
			self.tasks.append(self.loop.create_task(self.thisAppController.subscribeToID(entryText)))
			
		else:
			self.errorMessageLabel["text"] = "Only Alphanumeric Characters"		
			
	def inGameUI(self, entryText):
		if (self.currentGroupIDWindow == None):
			self.currentGroupIDWindow = tkinter.Frame(self)
			self.currentGroupIDWindow.pack(side="top")
			groupIDPreLabel = tkinter.Label(self.currentGroupIDWindow, text = "Current Room: ")
			groupIDPreLabel.pack(side="left")
			self.groupIDLabel = tkinter.Label(self.currentGroupIDWindow, text = entryText)
			self.groupIDLabel.pack(side="left")
		else:
			self.groupIDLabel['text'] = entryText
		
				
	def updater(self, interval):
		self.update()
		self.loop.call_later(interval, self.updater, interval)
		
	def close(self):
		self.loop.stop()
		sys.exit()