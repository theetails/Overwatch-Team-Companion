from PIL import ImageGrab, Image
import numpy as np
from scipy.misc import imresize
from functools import reduce
from os import listdir
import collections
from collections import Counter
import operator
import subprocess as sp
import asyncio
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
import json
import time

from Game import Game
	
class AppController(ApplicationSession):
	
	heroesArray = {"searching": "blank", "unknown": "blank", "dva": 1, "reinhardt": 2, "roadhog": 3, "winston": 4, "zarya": 5, "tracer": 6, "mccree": 7, "pharah": 8, "reaper": 9, "soldier76": 10, "genji": 11, "bastion": 12, "hanzo": 13, "junkrat": 14, "mei": 15, "torbjorn": 16, "widowmaker": 17, "lucio": 18, "mercy": 19, "symmetra": 20, "zenyatta": 21, "ana": 22, "sombra": 23}
	mapDictionary = {"dorado": "escort", "eichenwalde": "transition", "hanamura": "assault", "hollywood": "transition", "ilios": "control", "king's row": "transition", "lijiang": "control", "nepal": "control", "numbani": "transition", "oasis": "control", "route66": "escort", "temple of anubis": "assault", "volskaya industries": "assault", "watchpoint gibraltar": "escort"}
	subscriptionString = ""
	previousHeroesInitial = [["blank", "blank", "blank", "blank", "blank", "blank"], ["blank", "blank", "blank", "blank", "blank", "blank"]]
	previousHeroes = previousHeroesInitial
	previousMap = ""
	previousMapType = ""
	previousMapSide = ""
	
		
	def threshold(self, imageArray):
		balanceArray = []
		newArray = imageArray.copy()
		newArray.setflags(write=1)
		
		for eachRow in imageArray:
			for eachPixel in eachRow:
				avgNum = reduce(lambda x, y: int(x) + int(y), eachPixel[:3])/3
				balanceArray.append(avgNum)
		balance = reduce(lambda x, y: x + y, balanceArray)/len(balanceArray)
		
		#balance = 110
		for rowNumber,eachRow in enumerate(newArray):
			for pixelNumber,eachPixel in enumerate(eachRow):
				if reduce(lambda x, y: int(x) + int(y), eachPixel[:3])/3 > balance:
					newArray[rowNumber][pixelNumber] = [255,255,255] #White
				else: 
					newArray[rowNumber][pixelNumber] = [0,0,0] #Black
		return newArray

	def readReferences(self, filename): #moved
		referenceImageFile = open(filename, 'r').read()
		referenceImageFile = referenceImageFile.split('\n')
		referenceImageDictionary = dict()
		for referenceImage in referenceImageFile:
			if len(referenceImage) > 1:
				imageString = referenceImage.split('::') #0 is name, 1 is pixel arrays
				if imageString[0] not in referenceImageDictionary:
					referenceImageDictionary[imageString[0]] = []
				splitString = imageString[1].split('],')
				referenceImageDictionary[imageString[0]].append(splitString)
		return referenceImageDictionary

	def openReferences(self): #moved
		characterReferences = self.readReferences("Array.txt")
		mapReferences = self.readReferences("MapArray.txt")
		mapReferencesLijiang = self.readReferences("MapArrayLijiang.txt")
		
		return characterReferences, mapReferences, mapReferencesLijiang

	def readScreen(self, imgArray, mode):
		numRows = 2
		startX = 441
		endX = 518
		startY = 595
		endY = 637
		topStartY = 290
		topEndY = 332
		
		if mode == "feeler":
			numRows = 1
			endHeroSlot = 1
		elif mode == "feelerCharSelect":
			numRows = 1
			endHeroSlot = 1
			startY = 624
			endY = 666
		elif mode == "all":
			endHeroSlot = 6
		elif mode == "finishCharSelect":
			numRows = 1
			startY = 624
			endY = 666
			endHeroSlot = 6
		else:
			endHeroSlot = 6
		
		collection = []
		counter = 1;
		for j in range (0,numRows):
			for i in range (0,endHeroSlot):
				if ( ((mode == "finish") or (mode == "finishCharSelect")) and (j == 0) and (i == 0) ):
					startX = startX + 192
					endX = endX + 192
				else:
					#img = ImageGrab.grab(bbox=(startX,startY,endX,endY)) #bbox specifies specific region (bbox= x,y,width,height)
					thisCharImg = imgArray[startY:endY, startX:endX]
					imgArrayThreshold = self.threshold(np.asarray(thisCharImg))
					collection.append(imgArrayThreshold)
					startX = startX + 192
					endX = endX + 192
					if mode == "all":
						#to save for testing
						img = Image.fromarray(imgArrayThreshold)
						img.save("C:\\Users\\Voxter\\Desktop\\Overwatch Python App\\Test\\screenshot"+str(counter)+".png", "PNG")
						counter += 1
			startX = 441
			endX = 518
			startY = topStartY
			endY = topEndY
		return collection	

	def identifyMap(self, screenImgArray, mapImageDictionary, mapImageLijiangDictionary):
		thisMap = self.getMap(screenImgArray, "standard")
		potential = self.whatCharacterIsThis(thisMap, mapImageDictionary)
		thisMap = max(potential.keys(), key=(lambda k: potential[k]))
		print(potential[thisMap])
		if (potential[thisMap] > 1900):
			if (thisMap == "lijiang tower"):
				thisMap = self.getMap(screenImgArray, "lijiang")
				potential = self.whatCharacterIsThis(thisMap, mapImageLijiangDictionary)
				thisMap = max(potential.keys(), key=(lambda k: potential[k]))
				thisMap = "lijiang-"+thisMap
			print(thisMap)
			thisMapSplit = thisMap.split("-")
			thisMapType = self.mapDictionary[thisMapSplit[0]]
		else:
			if (self.previousMap != ""):
				thisMap = self.previousMap
			else:
				thisMap = "unknown"
		return thisMap

	def getMap(self, imgArray, mode):
		startX = 60
		endX = 290
		if (mode == "lijiang"):
			startX = 294 #lijiang subsection
			endX = 420 #lijiang subsection
		startY = 168
		endY = 206
		mapImage = imgArray[startY:endY, startX:endX]
		mapImageArray = np.asarray(mapImage)
		resizedImageArray = imresize(mapImageArray,(19,115))
		
		newImageArray = self.threshold(resizedImageArray)
		if (mode == "reference"):
			img = Image.fromarray(newImageArray)
			img.save("C:\\Users\\Voxter\\Desktop\\Overwatch Python App\\Test\\map.png", "PNG")
		return newImageArray

	def checkFirstCharacter(self, referenceImageDictionary, screenImgArray, mode):
		collectedImage = self.readScreen(screenImgArray, mode) #check if pressing tab at standard screen
		potential = self.whatCharacterIsThis(collectedImage[0], referenceImageDictionary)
		character = max(potential.keys(), key=(lambda k: potential[k]))
		if (potential[character] > 2800):
			return character
		else: 
			return False

	def identifyCharacters(self, referenceImageDictionary, firstCharacter, screenImgArray, readScreenMode):
		heroesList = [[],[]]
		print (firstCharacter)
		characterSplit = firstCharacter.split("-")
		characterID = self.heroesArray[characterSplit[0]]
		heroesList[0].append(characterID)
				
		collectedImages = self.readScreen(screenImgArray,readScreenMode)
		currentTime = str(int(time.time()))
		fullscreenSave = False
		for characterNumber, unknownCharacter in enumerate(collectedImages):	
			thisNumber = characterNumber + 2
			if (thisNumber > 6):
				thisRow = 1
			else :
				thisRow = 0
			potential = self.whatCharacterIsThis(unknownCharacter, referenceImageDictionary)
			thisCharacter = max(potential.keys(), key=(lambda k: potential[k]))
			if (potential[thisCharacter] < 2800):
				if (thisNumber > 6):
					previousHeroNumber = thisNumber - 6
				else:
					previousHeroNumber = thisNumber
				thisCharacterNumber=self.previousHeroes[thisRow][previousHeroNumber - 1]
				thisCharacter = list(self.heroesArray.keys())[list(self.heroesArray.values()).index(thisCharacterNumber)]
				print (thisCharacter + " (previous)")
				if (readScreenMode != "finishCharSelect"):					
					#print(potential)
					path = "Debug"
					
					#save image
					img = Image.fromarray(unknownCharacter)
					img.save(path+"\\Potential " + currentTime + " " + str(thisNumber) + ".png", "PNG")
					if (fullscreenSave==False):
						screenshot = Image.fromarray(screenImgArray)
						screenshot.save(path+"\\Potential " + currentTime + " fullscreen" + ".png", "PNG")
						fullscreenSave = True
					#save potential
					debugFile = open(path+'\\Potential ' + currentTime + " " + str(thisNumber) + '.txt','w')
					#potentialSorted = collections.OrderedDict(sorted(potential.items(), operator.itemgetter(1), True))
					for potentialCharacter, value in sorted(potential.items(), key = operator.itemgetter(1), reverse = True):
						lineToWrite = str(value)+': '+potentialCharacter+'\n'
						debugFile.write(lineToWrite)

			else: 
				print (thisCharacter)
			characterSplit = thisCharacter.split("-")
			characterID = self.heroesArray[characterSplit[0]]
			heroesList[thisRow].append(characterID)
		
		return heroesList

	def identifySide(self, screenImgArray):
		pixelToCheck = screenImgArray[95][95]
		red = pixelToCheck[0]
		green = pixelToCheck[1]
		blue = pixelToCheck[2]
		#print(red)
		#print(green)
		#print(blue)
		if ((red > 200) and (green < 200) and (blue < 200)):
			thisSide = "offense"
		elif ((red < 200) and (green > 180) and (blue > 100)):
			thisSide = "defense"
		else: 
			thisSide = self.previousMapSide
			print ("neither")
			print (red)
			print (green)
			print (blue)
		
		print (thisSide)
		return thisSide

	def broadcastHeroes(self, heroesList):
		publishList = ["heroes",heroesList]
		self.publish(self.subscriptionString, publishList)
		
	def broadcastOptions(self, thisMap):
		optionsToSend = ["options", thisMap]
		self.publish(self.subscriptionString, optionsToSend)
	
	def findCharacters(self, characterImageDictionary, mapImageDictionary, mapImageLijiangDictionary):
		screenImg = ImageGrab.grab(bbox=None)
		screenImgArray = np.asarray(screenImg)
		character = self.checkFirstCharacter(characterImageDictionary, screenImgArray, "feeler")
		
		if (character != False):
			tmp = sp.call('cls',shell=True) #clear cmd screen
			heroesList = self.identifyCharacters(characterImageDictionary, character, screenImgArray, "finish")
			if (heroesList != self.previousHeroes):
				self.previousHeroes = heroesList
				self.broadcastHeroes(heroesList)
			return 2
		else: #check if this is the character select screen
		
			character = self.checkFirstCharacter(characterImageDictionary, screenImgArray, "feelerCharSelect")
			if (character != False): #check character select screen
				tmp = sp.call('cls',shell=True) #clear cmd screen
				side = self.identifySide(screenImgArray)
				map = self.identifyMap(screenImgArray, mapImageDictionary, mapImageLijiangDictionary)
				mapSplit = map.split("-")
				if (map != "unknown"):
					type = self.mapDictionary[mapSplit[0]]
					#temporary until detecting during tab
					if (type == "transition"):
						type = "assault"
				else:
					type = "control"
				print(type)
				
				thisMap = [];
				thisMap.append(side)
				#side options: offense, defense
				thisMap.append(type)
				#type options: escort, assault, control
				thisMap.append("competitive")
				
				if (map != self.previousMap):
					previousMapSplit = self.previousMap.split("-")
					#check if another point on control map, rather than an entirely new map
					if ((mapSplit[0] != previousMapSplit[0])):
						#if it is not another point on the same control map
						self.broadcastOptions(thisMap)
						self.previousMapSide = side
						self.previousMapType = type
						self.previousHeroes = self.previousHeroesInitial
					self.previousMap = map
				elif (side != self.previousMapSide):
					self.previousMapSide = side
					self.broadcastOptions(thisMap)
				elif (type != self.previousMapType):
					self.previousMap = thisMap
					self.broadcastOptions(thisMap)
					
				heroesList = self.identifyCharacters(characterImageDictionary, character, screenImgArray, "finishCharSelect")
				#Keep Previous Enemy Team
				if (len(self.previousHeroes) == 2):
					heroesList[1] = self.previousHeroes[1]
				self.broadcastHeroes(heroesList)	
					
				
				return 4
			else:
				return .5
		
	def whatCharacterIsThis(self, capturedImage, referenceImagesDictionary):
		matchedArray = []
		
		capturedImageList = capturedImage.tolist()
		capturedImageString = str(capturedImageList)
		capturedImagePixels = capturedImageString.split('],')
		
		for characterName, referenceImages in referenceImagesDictionary.items():
			x = 0
			for referencePixels in referenceImages:
				while x < len(referencePixels):
					#for referencePixel in referenceImage:
					#print("Reference Pixel: "+referencePixels[x]+" "+"Captured Pixel: "+capturedImagePixels[x])
					if referencePixels[x]==capturedImagePixels[x]:
						matchedArray.append(characterName)
					x += 1
		count = Counter(matchedArray)
		return count

	#@asyncio.coroutine
	def onJoin(self, details):
		# 1. subscribe to a topic so we receive events
		#def onevent(msg):
			#print("Got event: {}".format(msg))
		
		#yield self.subscribe(onevent, subscriptionString)
		#self.publish(u'subscriptionString',"test")
		#print ("published")
		#asyncio.get_event_loop().stop()

		# 2. publish an event to a topic
		# self.publish('com.myapp.hello', 'Hello, world!')
		
		gameObject = Game()
		
		subscriptionID = input("Enter your Session ID:")
	
		self.subscriptionString	= 'com.voxter.teambuilder.'+subscriptionID
		
		tmp = sp.call('cls',shell=True)
		characterImageList, mapImageList, MapImageLijiangList = self.openReferences()
		while True:
			sleepTime = self.findCharacters(characterImageList, mapImageList, MapImageLijiangList)
			yield from asyncio.sleep(sleepTime)

def createReferences():
	referenceImagesFile = open('Array.txt','w')
	path = "Reference\\Image Sources"
	referenceImages = [image for image in listdir(path)]
	for file in referenceImages:
		imagePath = path+"/"+file
		sourceImage = Image.open(imagePath)
		sourceImageArray = np.array(sourceImage)
		thresholdImageArray = MyComponent().threshold(sourceImageArray)
		sourceImageList = str(thresholdImageArray.tolist())
		lineToWrite = file[:-4]+'::'+sourceImageList+'\n'
		referenceImagesFile.write(lineToWrite)

def createMapReferenceImages():
	screenImg = ImageGrab.grab(bbox=None)
	screenImgArray = np.asarray(screenImg)
	thisMap = MyComponent().getMap(screenImgArray, "reference")

def createMapReferences():
	referenceImagesFile = open('MapArray.txt','w')
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
	referenceImagesFile2 = open('MapArrayLijiang.txt','w')
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

def createReferenceSourceImages():
	screenImg = ImageGrab.grab(bbox=None)
	screenImgArray = np.asarray(screenImg)
	MyComponent().readScreen(screenImgArray,"all")

def unitTestReferences():
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



#createReferenceSourceImages()
#createReferences()
#createMapReferenceImages()
#createMapReferences()
#unitTestReferences()
#mainFunction()
gameObject = Game()

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
Rework this to be object oriented -> (each hero has a hero, previous hero, potential, etc)
Javascript -> Object Oriented
Allow two secondary healers instead of a primary
Smart Flanker selection (flanker could also be a front line)
Same for Main Tanks / Secondary
Keep track of Game Time
	- Improve Overall Flow of code in relation to game flow
Identify current objective - transition maps
Identify Objective Progress
Streaming Integration
Stats Tracking
Login System
Sound Alerts
GUI

'''



