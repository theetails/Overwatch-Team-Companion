from PIL import Image
import numpy as np
from scipy.misc import imresize
import operator
import subprocess as sp

from GameObject import GameObject

class MapInfo(GameObject):
	
	mapDictionary = {"dorado": "escort", "eichenwalde": "transition", "hanamura": "assault", "hollywood": "transition", "ilios": "control", "king's row": "transition", "lijiang": "control", "nepal": "control", "numbani": "transition", "oasis": "control", "route66": "escort", "temple of anubis": "assault", "volskaya industries": "assault", "watchpoint gibraltar": "escort", "black forest": "arena", "castillo": "arena", "ecopoint antarctica": "arena", "necropolis": "arena"}
	currentMap = [None]
	currentMapType = "escort"
	currentMapSide = "offense"
	mapChange = False
	
	previousMap = [None]
	previousMapType = None
	previousMapSide = None
	
	currentImageArray = None
	potential = None
	thisMapPotential = None
	previousImageArray = None
	previousPotential = None
	
	imageThreshold = {"Hero Select": 1900, "Tab": 1700}
	
	def __init__(self, debugMode):
		self.debugMode = debugMode
		self.mapReferences = self.readReferences("Reference\\MapImageList.txt")
		self.mapReferencesLijiang = self.readReferences("Reference\\MapImageListLijiang.txt")
		self.mapReferencesTab = self.readReferences("Reference\\MapImageListTab.txt")
	
	def main(self, screenImageArray):
		sp.call('cls',shell=True)
		# check if Tab View
		mapResult = self.identifyMap(screenImageArray, "Tab")
		if (mapResult):
			typeResult = self.identifyMapType()
			return "Tab"
		else:
			#check if Hero Select View
			mapResult = self.identifyMap(screenImageArray, "Hero Select")
			if (mapResult):
				typeResult = self.identifyMapType()
				return "Hero Select"
			else:
				return False
		
	def mapType(self):
		return self.mapDictionary[self.currentMap[0]]
	
	def identifyMap(self, screenImgArray, view):
		thisMapArray = self.getMap(screenImgArray, view, False)
		if (view == "Hero Select"):
			potential = self.whatImageIsThis(thisMapArray, self.mapReferences)
		elif (view == "Tab"):
			potential = self.whatImageIsThis(thisMapArray, self.mapReferencesTab)
		thisMap = max(potential.keys(), key=(lambda k: potential[k]))
		self.previousImageArray = self.currentImageArray
		self.currentImageArray = thisMapArray
		self.previousPotential = self.potential
		self.potential = potential
		self.thisMapPotential = potential[thisMap]
		print(potential[thisMap])
		
		if (potential[thisMap] > self.imageThreshold[view]):
			if (thisMap == "lijiang tower" and view == "Hero Select"):
				thisMap = self.getMap(screenImgArray, "Hero Select", True)
				potential = self.whatImageIsThis(thisMap, self.mapReferencesLijiang)
				thisMap = max(potential.keys(), key=(lambda k: potential[k]))
				thisMap = "lijiang-"+thisMap
			thisMapSplit = thisMap.split("-")
			if (self.currentMap != thisMapSplit):
				self.mapChange = True
			else:
				self.mapChange = False
			self.previousMap = self.currentMap
			self.currentMap = thisMapSplit
			print(thisMap)
			return True
		else:
			if (self.previousMap != [None]):
				thisMap = self.previousMap[0]
			else:
				thisMap = "unknown"
			return False
		
	def identifyMapType(self):
		if (self.currentMap[0] != self.previousMap[0]):
			if (self.currentMap[0] != "unknown"):
				thisMapType = self.mapType()
				#temporary until detecting during tab
				if (thisMapType == "transition"):
					thisMapType = "assault"
			else:
				thisMapType = "control"
	
			self.previousMapType = self.currentMapType
			self.currentMapType = thisMapType
			returnValue = True
		else:
			returnValue = False
		
		print(self.currentMapType)
		return returnValue
		
	def saveDebugData(self, currentTime):
		path = "Debug"
		
		#save image
		img = Image.fromarray(self.currentImageArray)
		img.save(path+"\\Potential " + currentTime + " map.png", "PNG")
		if (currentTime != "for_reference"):
			#save potential
			debugFile = open(path+"\\Potential " + currentTime + " map.txt",'w')
			for potentialMap, value in sorted(self.potential.items(), key = operator.itemgetter(1), reverse = True):
				lineToWrite = str(value)+': '+potentialMap+'\n'
				debugFile.write(lineToWrite)
			
	def getMap(self, imgArray, mode, lijiang):
		if (mode == "Hero Select"):
			startX = 60
			endX = 290
			if (lijiang):
				startX = 294 #lijiang subsection
				endX = 420 #lijiang subsection
			startY = 168
			endY = 206
		elif (mode == "Tab"):
			startX = 105
			endX = 240
			startY = 50
			endY = 63
		mapImage = imgArray[startY:endY, startX:endX]
		mapImageArray = np.asarray(mapImage)
		if (mode == "Hero Select"):
			resizedImageArray = imresize(mapImageArray,(19,115))
		elif (mode == "Tab"):
			resizedImageArray = mapImageArray
		newImageArray = self.threshold(resizedImageArray)
		return newImageArray
	
	def identifySide(self, imgArray):
		pixelToCheck = imgArray[95][95]
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
		
		if (thisSide != self.previousMapSide):
			self.previousMapSide = self.currentMapSide
			self.currentMapSide = thisSide
			return True
		else: 
			return False
	
	def broadcastOptions(self, broadcaster):
		thisMap = [];
		thisMap.append(self.currentMapSide)
		#side options: offense, defense
		thisMap.append(self.currentMapType)
		#type options: escort, assault, control
		thisMap.append("single_hero")
		
		optionsToSend = ["options", thisMap]
		if (broadcaster != "debug"):
			broadcaster.publish(broadcaster.subscriptionString, optionsToSend)
			
			
			
			