from PIL import ImageGrab
import numpy as np
import time

from AllHeroes import AllHeroes
from MapInfo import MapInfo

class Game:

	def __init__(self, debugMode):
		self.debugMode = debugMode
		self.heroes = AllHeroes(debugMode)
		self.map = MapInfo(debugMode)
	
	def main(self, broadcaster):
		screenImgArray = self.getScreen()
		currentTime = str(int(time.time()))
		currentView = self.heroes.main(screenImgArray, currentTime) #getHeroes - return View
		
		if (currentView == "Tab"):
			sleepTime = 2
			
			heroesChanged = self.heroes.checkForChange()
			if (heroesChanged):
				self.heroes.broadcastHeroes(broadcaster)
		elif (currentView == "Hero Select"):
			sleepTime = 3
			
			mapIdentified = self.map.identifyMap(screenImgArray) #check Map, return if change
			sideIdentified = self.map.identifySide(screenImgArray)
			if ((self.map.thisMapPotential < self.map.imageThreshold) and self.debugMode):
				self.map.saveDebugData(currentTime)
			if (mapIdentified or sideIdentified):
				self.map.broadcastOptions(broadcaster)
			if (mapIdentified):
				self.heroes.clearEnemyHeroes(broadcaster)
			elif(sideIdentified):
				heroesChanged = self.heroes.checkForChange()
				if (heroesChanged):
					self.heroes.broadcastHeroes(broadcaster)
			else: 
				heroesChanged = self.heroes.checkForChange()
				if (heroesChanged):
					self.heroes.broadcastHeroes(broadcaster)
		else:
			sleepTime = 0.5
			heroesChanged = self.heroes.checkForChange()
			if (heroesChanged):
				self.heroes.broadcastHeroes(broadcaster)
			
		return sleepTime
		
	def getScreen(self):
		screenImg = ImageGrab.grab(bbox=None)
		return np.asarray(screenImg)
