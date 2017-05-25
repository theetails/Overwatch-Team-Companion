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
		self.groupIDDisplayWindow = None
		self.thisAppController = thisAppController
		self.updater(interval)
		
	async def startUI(self):
		self.resizable(width=False, height=False)
		self.title("Main Menu")
		self.mainMenuWindow = tkinter.Frame(self, width=self.width, height=self.height)
		self.mainMenuWindow.pack(fill="both", expand=True, padx=20, pady=20)
		startMainFunctionButton = tkinter.Button (self.mainMenuWindow, text = "Start Game Watcher", command = self.getGroupID).pack(fill = "x")
		createHeroReferenceImagesButton = tkinter.Button (self.mainMenuWindow, text = "Hero Reference: Create Images", command = self.createHeroImages).pack(fill = "x")
		createHeroReferencesButton = tkinter.Button (self.mainMenuWindow, text = "Hero Reference: Create TXT", command = self.createHeroReference).pack(fill = "x")
		createMapReferenceImagesButton = tkinter.Button (self.mainMenuWindow, text = "Map Reference: Create Image", command = self.createMapImage).pack(fill = "x")
		createMapReferencesButton = tkinter.Button (self.mainMenuWindow, text = "Map Reference: Create TXT", command = self.createMapReference).pack(fill = "x")
	
	def getGroupID(self):
		self.mainMenuWindow.destroy()
		self.title("Group ID Input")
		errorWindow = tkinter.Frame(self)
		errorWindow.pack(side="bottom", fill=tkinter.X, expand=True, padx=20)
		groupIDEntryWindow = tkinter.Frame(self, width=self.width, height=self.height)
		groupIDEntryWindow.pack(side="bottom", fill=tkinter.X, expand=True, padx=20)
		groupIDEntryLabel = tkinter.Label(groupIDEntryWindow, text = "Group ID")
		groupIDEntryLabel.pack(side="left")
		groupIDEntry = tkinter.Entry(groupIDEntryWindow, width = 20)
		groupIDEntry.pack(side="left")
		submitGroupID = tkinter.Button(groupIDEntryWindow, text = "Submit", command = lambda: self.checkGroupID(groupIDEntry))
		submitGroupID.pack(side="left")
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
			self.wm_state('iconic')
			self.currentGroupID = entryText
			self.errorMessageLabel["text"] = ""
			self.inRoomUI(entryText)
			self.tasks.append(self.loop.create_task(self.thisAppController.subscribeToID(entryText)))
			
		else:
			self.errorMessageLabel["text"] = "Only Alphanumeric Characters"		
			
	def inRoomUI(self, entryText):
		if (self.groupIDDisplayWindow == None):
			self.groupIDDisplayWindow = tkinter.Frame(self)
			self.groupIDDisplayWindow.pack(side="top", fill=tkinter.X, expand=True, padx=20)
			groupIDDisplayLabel = tkinter.Label(self.groupIDDisplayWindow, text = "Current Room: ")
			groupIDDisplayLabel.pack(side="left")
			self.groupIDLabel = tkinter.Label(self.groupIDDisplayWindow, text = entryText)
			self.groupIDLabel.pack(side="left")
		else:
			self.groupIDLabel['text'] = entryText
	
	def createHeroImages(self):
		self.thisAppController.createImagesForHeroReference()
		
	def createHeroReference(self):
		self.thisAppController.createHeroReferences()
		
	def createMapImage(self):
		self.thisAppController.createImagesForMapReference()
		
	def createMapReference(self):
		self.thisAppController.createMapReferences()
				
	def updater(self, interval):
		self.update()
		self.loop.call_later(interval, self.updater, interval)
		
	def close(self):
		self.loop.stop()
		sys.exit()