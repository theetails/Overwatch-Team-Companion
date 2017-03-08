from PIL import ImageGrab, Image
import numpy as np
from os import listdir
import subprocess as sp
import asyncio
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner

from Game import Game
from GameObject import GameObject #not for main function
	
class AppController(ApplicationSession):

	
		
	@asyncio.coroutine
	async def onJoin(self, details):
		
		#Initialize Game Object & obtain Subscription String
		self.gameObject = Game()
		subscriptionID = input("Enter your Session ID:")
		self.subscriptionString	= 'com.voxter.teambuilder.'+subscriptionID
		tmp = sp.call('cls',shell=True)
		
		# Subscribe to the room so we receive events
		def onEvent(msg1, msg2=None):
			#debug output
			if (msg2 == None):
				print("Got event: Argument 1: {" + str(msg1) + "}")
			else:
				print("Got event: Argument 1: {" + str(msg1) + "} Argument 2: {" + str(msg2) + "}")
			
			if (msg1 == "Hello"):
				self.gameObject.heroes.broadcastHeroes(self)
				self.gameObject.map.broadcastOptions(self)
			elif (msg1 == "heroes"):
				self.gameObject.heroes.changeHeroes(msg2)
		
		await self.subscribe(onEvent, self.subscriptionString)
		
		#self.publish(u'subscriptionString',"test")
		#print ("published")
		#asyncio.get_event_loop().stop()
		
		
		while True:
			sleepTime = self.gameObject.main(self)
			await asyncio.sleep(sleepTime)

#supplementary functions

def createHeroReferences():
	thisGameObject = Game()

	referenceImagesFile = open('Reference\\HeroImageList.txt','w')
	path = "Reference\\Image Sources"
	referenceImages = [image for image in listdir(path)]
	for file in referenceImages:
		imagePath = path+"/"+file
		sourceImage = Image.open(imagePath)
		sourceImageArray = np.array(sourceImage)
		thresholdImageArray = thisGameObject.heroes.threshold(sourceImageArray)
		sourceImageList = str(thresholdImageArray.tolist())
		lineToWrite = file[:-4]+'::'+sourceImageList+'\n'
		referenceImagesFile.write(lineToWrite)

def createImagesForHeroReference():
	thisGameObject = Game()
	screenImgArray = thisGameObject.getScreen()
	for heroNumber in range(1,13):
		hero = thisGameObject.heroes.heroesDictionary[heroNumber]
		thisGameObject.heroes.identifyHero(screenImgArray, hero, "Tab") # "Tab" or "Hero Select"
		hero.saveDebugData("for_reference")

def createImagesForMapReference(): #needs reworked
	screenImg = ImageGrab.grab(bbox=None)
	screenImgArray = np.asarray(screenImg)
	thisMap = MyComponent().getMap(screenImgArray, "reference")

def createMapReferences(): #needs reworked
	referenceImagesFile = open('Reference\\MapImageList.txt','w')
	path = "Reference\\Map Name Image Sources"
	referenceImages = [image for image in listdir(path)]
	for file in referenceImages:
		imagePath = path+"/"+file
		sourceImage = Image.open(imagePath)
		sourceImageArray = np.array(sourceImage)
		thresholdImageArray = MyComponent().threshold(sourceImageArray)
		sourceImageList = str(thresholdImageArray.tolist())
		lineToWrite = file[:-4]+'::'+sourceImageList+'\n'
		referenceImagesFile.write(lineToWrite)
	
	#repeat for Lijiang
	referenceImagesFile2 = open('Reference\\MapImageListLijiang.txt','w')
	path = "Reference\\Lijiang Map Name Image Sources"
	referenceImages = [image for image in listdir(path)]
	for file in referenceImages:
		imagePath = path+"/"+file
		sourceImage = Image.open(imagePath)
		sourceImageArray = np.array(sourceImage)
		thresholdImageArray = MyComponent().threshold(sourceImageArray)
		sourceImageList = str(thresholdImageArray.tolist())
		lineToWrite = file[:-4]+'::'+sourceImageList+'\n'
		referenceImagesFile2.write(lineToWrite)



def unitTestReferences(): #needs reworked
	referenceImageList, temp1, temp2 = openReferences() #need to add maps

	path = "Reference\\Image Sources"
	referenceImages = [image for image in listdir(path)]
	for file in referenceImages:
		imagePath = path+"/"+file
		sourceImage = Image.open(imagePath)
		sourceImageArray = np.array(sourceImage)
		thresholdImageArray = threshold(sourceImageArray)
		potential = whatCharacterIsThis(thresholdImageArray, referenceImageList)
		character = max(potential.keys(), key=(lambda k: potential[k]))
		print(file)
		print (character)
		print (potential)
		print ("")

def mainFunction():
	runner = ApplicationRunner(url="ws://voxter.mooo.com:8080/ws", realm="com.voxter.teambuilder")
	runner.run(AppController) 

#createImagesForHeroReference()
#createHeroReferences()
#createImagesForMapReference()
#createMapReferences()
#unitTestReferences()
mainFunction()

'''
dual assault points:
17 x 17
1st: 
	x: 919
	y: 110
2nd:
	x: 989
	y: 108

'''
'''
To Do:
teams.js
	Javascript -> Object Oriented
	Allow two secondary healers instead of a primary
	Smart Flanker selection (flanker could also be a front line)
	Same for Main Tanks / Secondary
overwatch_app.py	
	Detect Screen Resolution - Currently only 1080p
	Detect Screen Color Differences
	Identify current objective - transition maps
	Keep track of Game Time
	Identify Objective Progress
	Streaming Integration
	Stats Tracking
	Login System
	Sound Alerts (?)
	GUI

'''



