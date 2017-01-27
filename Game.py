from PIL import ImageGrab
import numpy as np
import time

from AllHeroes import AllHeroes
from MapInfo import MapInfo

class Game:

	def __init__(self):
		self.heroes = AllHeroes()
		self.map = MapInfo()
		print("Initialized")
	
	def main(self, broadcaster):
		screenImg = ImageGrab.grab(bbox=None)
		screenImgArray = np.asarray(screenImg)
		currentTime = str(int(time.time()))
		currentView = self.heroes.main(screenImgArray, currentTime, broadcaster) #getHeroes - return View
		
		if (currentView == "Tab"):
			sleepTime = 2
			
			heroesChanged = self.heroes.checkForChange()
			if (heroesChanged):
				self.heroes.broadcastHeroes(broadcaster)
		elif (currentView == "Hero Select"):
			sleepTime = 3
			
			mapIdentified = self.map.identifyMap(screenImgArray) #check Map, return if change
			sideIdentified = self.map.identifySide(screenImgArray)
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
