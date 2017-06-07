from PIL import ImageGrab
import numpy as np
import time
import subprocess as sp

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
		currentView = self.map.main(screenImgArray)
		if (currentView):
			sp.call('cls',shell=True)
			print(self.map.currentMap[0])
			print(currentView)
			if (currentView == "Tab"):
				sleepTime = 0.5
				self.map.identifyObjectiveProgress(screenImgArray)
			elif (currentView == "Hero Select"):
				sleepTime = 1
			self.heroes.main(screenImgArray, currentTime, currentView)
			
			mapChanged = self.map.mapChange
			if (currentView == "Hero Select"):
				sideChanged = self.map.identifySide(screenImgArray)
			else:
				sideChanged = False
			if ((self.map.thisMapPotential < self.map.imageThreshold[currentView]) and self.debugMode):
				self.map.saveDebugData(currentTime)
			if (mapChanged or sideChanged):
				self.map.broadcastOptions(broadcaster)
				self.map.resetObjectiveProgress()
			if (mapChanged and currentView == "Hero Select"):
				print("ClearEnemyHeroes")
				self.heroes.clearEnemyHeroes(broadcaster)
			elif(sideChanged):
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
				
			# Check for Objective Progress Here
			self.map.identifyObjectiveProgress(screenImgArray)
			
		return sleepTime
		
	def getScreen(self):
		screenImg = ImageGrab.grab(bbox=None)
		return np.asarray(screenImg)
