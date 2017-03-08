import operator
from PIL import Image

class Hero:
	heroesReferenceDictionary = {"unknown": "blank", "searching": "blank", "dva": 1, "reinhardt": 2, "roadhog": 3, "winston": 4, "zarya": 5, "tracer": 6, "mccree": 7, "pharah": 8, "reaper": 9, "soldier76": 10, "genji": 11, "bastion": 12, "hanzo": 13, "junkrat": 14, "mei": 15, "torbjorn": 16, "widowmaker": 17, "lucio": 18, "mercy": 19, "symmetra": 20, "zenyatta": 21, "ana": 22, "sombra": 23, "orisa": 24}
	
	currentHero = None
	previousHero = None
	
	screenPositionTab = None
	screenPositionCharacterSelect = None
	
	currentImageArray = None
	potential = None
	previousImageArray = None
	previousPotential = None
	
	
	def __init__(self, thisSlotNumber):
		self.slotNumber = thisSlotNumber
		self.calculateScreenPosition()
		
	def calculateScreenPosition(self):
		
		characterSelectStartY = 624
		characterSelectEndY = 666
		
		if (self.slotNumber <= 6):
			startY = 595
			endY = 637
			xHeroNumber = self.slotNumber
		else:
			startY = 290
			endY = 332
			xHeroNumber = self.slotNumber - 6
			
		startX = 249 + (xHeroNumber * 192)
		endX = 326 + (xHeroNumber * 192)
		
		self.screenPositionCharacterSelect = {"startX": startX, "endX": endX, "startY": characterSelectStartY, "endY": characterSelectEndY}
		self.screenPositionTab = {"startX": startX, "endX": endX, "startY": startY, "endY": endY}
	
	def saveDebugData(self, currentTime):
		path = "Debug"
		
		#save image
		img = Image.fromarray(self.currentImageArray)
		img.save(path+"\\Potential " + currentTime + " " + str(self.slotNumber) + ".png", "PNG")
		#save potential
		debugFile = open(path+'\\Potential ' + currentTime + " " + str(self.slotNumber) + '.txt','w')
		for potentialCharacter, value in sorted(self.potential.items(), key = operator.itemgetter(1), reverse = True):
			lineToWrite = str(value)+': '+potentialCharacter+'\n'
			debugFile.write(lineToWrite)			
		
	def setPotential(self, thisPotential):
		self.previousPotential = self.potential
		self.potential = thisPotential
		
	def setImageArray(self, imageArray):
		self.previousImageArray = self.currentImageArray
		self.currentImageArray = imageArray
		
	def setHero(self, hero):
		self.previousHero = self.currentHero
		self.currentHero = hero
		
	def revertPreviousHero(self):
		if(self.previousHero != None):
			self.currentHero = self.previousHero
			self.previousHero = None
			self.potential = self.previousPotential
			self.previousPotential = None
			self.currentImageArray = self.previousImageArray
			self.previousImageArray = None
		
	def getHeroNumber(self):
		if (self.currentHero == None):
			return "blank"
		else:
			return self.heroesReferenceDictionary[self.currentHero]
			
	def getHeroNameFromNumber(self, heroNumber):
		for referenceName, referenceNumber in self.heroesReferenceDictionary.items():
			if (heroNumber == referenceNumber):
				return referenceName
		
	def clearHero(self):
		self.currentHero = None
		self.currentImageArray = None
		self.potential = None

		self.previousHero = None
		self.previousImageArray = None
		self.previousPotential = None
