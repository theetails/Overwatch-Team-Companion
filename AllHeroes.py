import numpy as np
import subprocess as sp
from PIL import Image

from GameObject import GameObject
from Hero import Hero

class AllHeroes(GameObject):
	
	correctHeroThreshold = 2850
	heroesDictionary = {}
	heroesList = []
	
	def __init__(self):
		self.characterReferences = self.readReferences("Reference\\HeroImageList.txt")
		for x in range(1,13):
			self.heroesDictionary[x] = Hero(x)
	
	def main(self, screenImageArray, currentTime):
		firstHero = self.heroesDictionary[1]
		tabView = self.identifyHero(screenImageArray, firstHero, "Tab")
		if (tabView == False):
			characterSelectView = self.identifyHero(screenImageArray, firstHero, "Character Select")
			if (characterSelectView == False):
				return "None"
			else:
				#Hero Select View
				heroRange = range(2,7)
				currentView = "Hero Select"
		else:
			#Tab View
			heroRange = range(2,13)
			currentView = "Tab"
		sp.call('cls',shell=True)
		print("Current View: " + currentView)
		print(firstHero.currentHero)
		
		failedHeroes = []
		for heroNumber in heroRange:
			thisHero = self.heroesDictionary[heroNumber]
			result = self.identifyHero(screenImageArray, thisHero, currentView)
			if (result == False):
				failedHeroes.append(heroNumber)
				print(str(heroNumber) + " Failed")
			else:
				print(thisHero.currentHero)
		
		if (len(failedHeroes) > 0):
			failedHeroes.append(1)
			for heroNumber in failedHeroes:
				self.heroesDictionary[heroNumber].saveDebugData(currentTime)
				self.heroesDictionary[heroNumber].revertPreviousHero()
			screenshot = Image.fromarray(screenImageArray)
			screenshot.save("Debug\\Potential " + currentTime + " fullscreen" + ".png", "PNG")
		
		# check for entire enemy team -> unknowns
		if (currentView == "Tab"):
			allUnknown = True
			for heroNumber, enemyHero in self.heroesDictionary.items():
				if (heroNumber in range(7,13)):
					if(enemyHero.currentHero != "unknown"):
						allUnknown = False
			del enemyHero
			if (allUnknown == True):
				for heroNumber, enemyHero in self.heroesDictionary.items():
					if (heroNumber in range(7,13)):
						enemyHero.revertPreviousHero()
		return currentView
	
	def heroesToList(self):
		currentHeroesList = [[],[]]
		
		for heroNumber, hero in self.heroesDictionary.items():
			if (heroNumber > 6):
				thisRow = 1
			else :
				thisRow = 0
			currentHeroesList[thisRow].append(hero.getHeroNumber())
		
		if (currentHeroesList != self.heroesList):
			self.heroesList = currentHeroesList
			return True
		else:
			return False
	
	def identifyHero(self, screenImgArray, thisHero, view):
		heroIdentities = {}
		if (view == "Tab"):
			heroCoordinates = thisHero.screenPositionTab
		else:
			heroCoordinates = thisHero.screenPositionCharacterSelect
		
		thisHeroImg = screenImgArray[ heroCoordinates["startY"] : heroCoordinates["endY"], heroCoordinates["startX"] : heroCoordinates["endX"]] #crop to Hero
		thisHeroImgThreshold = self.threshold(np.asarray(thisHeroImg)) #Make Black & White based off average value
		thisHero.setImageArray(thisHeroImg) #save IMG to Hero
		potential = self.whatImageIsThis(thisHeroImgThreshold, self.characterReferences) #compare to References
		thisHero.setPotential(potential)
		identifiedHero = max(potential.keys(), key=(lambda k: potential[k]))
		if (potential[identifiedHero] > self.correctHeroThreshold): #if enough pixels are the same
			thisHeroSplit = identifiedHero.split("-")
			thisHero.setHero(thisHeroSplit[0])
			if(thisHero.slotNumber==1 and thisHeroSplit[0] == "searching"): #The player cannot be "searching", reduces errors
				return False
			else: 
				return True
		else:
			return False
	
	def checkForChange(self):
		heroesListChange = self.heroesToList()  # Save heroes to heroesDictionary
		return heroesListChange
		
	def broadcastHeroes(self, broadcaster):
		publishList = ["heroes",self.heroesList]
		if (broadcaster != "debug"):
			broadcaster.publish(broadcaster.subscriptionString, publishList)
		
	
	def clearEnemyHeroes(self, broadcaster):
		for heroNumber, hero in self.heroesDictionary.items():
			if (heroNumber in range(7,13)):
				hero.clearHero()
		self.heroesToList()
		if (broadcaster != "debug"):
			self.broadcastHeroes(broadcaster)
		
	def changeHeroes(self, incomingHeroes):
		incomingHerosDictionary = {}
		count = 1
		for row in incomingHeroes:
			for heroNumber in row:
				incomingHerosDictionary[count]=heroNumber
				count = count + 1
		for heroNumber, hero in self.heroesDictionary.items():
			thisHeroName = hero.getHeroNameFromNumber(incomingHerosDictionary[heroNumber])
			hero.setHero(thisHeroName)
		self.heroesToList()
		
