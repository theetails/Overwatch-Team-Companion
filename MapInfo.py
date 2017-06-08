from PIL import Image
import numpy as np
from scipy.misc import imresize
import operator
import subprocess as sp
from functools import reduce
from pprint import pprint #temporary for debugging

from GameObject import GameObject

class MapInfo(GameObject):
	
	mapDictionary = {"dorado": "escort", "eichenwalde": "transition", "hanamura": "assault", "hollywood": "transition", "ilios": "control", "king's row": "transition", "lijiang": "control", "nepal": "control", "numbani": "transition", "oasis": "control", "route66": "escort", "temple of anubis": "assault", "volskaya industries": "assault", "watchpoint gibraltar": "escort", "black forest": "arena", "castillo": "arena", "ecopoint antarctica": "arena", "necropolis": "arena", "horizon lunar colony": "assault", "ilios well": "arena", "oasis city center": "arena", "oasis gardens": "arena"}
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

	imageThreshold = {"Hero Select": 1850, "Tab": 1700, "Assault": 135, "Control": 250, "Victory": 6500, "Defeat": 5800}
	
	def __init__(self, debugMode):
		self.debugMode = debugMode
		self.mapReferences = self.readReferences("Reference\\MapImageList.txt")
		self.mapReferencesLijiang = self.readReferences("Reference\\MapImageListLijiang.txt")
		self.mapReferencesTab = self.readReferences("Reference\\MapImageListTab.txt")
		self.assaultReference = self.readReferences("Reference\\ObjectiveListAssault.txt")
		self.controlReference = self.readReferences("Reference\\ObjectiveListControl.txt")
		self.gameEndReference = self.readReferences("Reference\\GameEnd.txt")
		
		self.resetObjectiveProgress()
		self.calculateAssaultProgressPixels()
	
	def main(self, screenImageArray):
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
	
	def resetObjectiveProgress(self):
		self.objectiveProgress = {}
		self.objectiveProgress["currentType"] = None
		self.objectiveProgress["gameEnd"] = False
		self.objectiveProgress["unlocked"] = False
		self.objectiveProgress["gameOver"] = False
	
	def calculateAssaultProgressPixels(self):
		assaultRadius = 23 #px
		self.assaultPixelsToCheck = []
		centerPoints = [[925,120],[1000,120]]
		pointNumber = 0
		for centerPoint in centerPoints:
			self.assaultPixelsToCheck.append([])
			for percentage in range(0,100):
				theta = -(percentage - 125)/(5/18)
				xCoordinate = int((np.cos(np.deg2rad(theta)) * assaultRadius) + centerPoint[0])
				if percentage > 50: #center isn't perfectly center
					xCoordinate = xCoordinate -1
				yCoordinate = int(-(np.sin(np.deg2rad(theta)) * assaultRadius) + centerPoint[1])
				if percentage > 25 and percentage < 75: #center isn't perfectly center
					yCoordinate = yCoordinate + 1
				#print (str(percentage) + " " + str(theta) + " " + str(xCoordinate) + " " + str(yCoordinate))
				self.assaultPixelsToCheck[pointNumber].append([xCoordinate,yCoordinate])
			pointNumber = pointNumber + 1
	
	def mapType(self):
		return self.mapDictionary[self.currentMap[0]]
	
	def identifyMap(self, screenImgArray, view):
		thisMapArray = self.getMap(screenImgArray, view, False)
		if (view == "Hero Select"):
			potential = self.whatImageIsThis(thisMapArray, self.mapReferences)
			self.objectiveProgress["gameEnd"] = None #delete me with proper flow
		elif (view == "Tab"):
			potential = self.whatImageIsThis(thisMapArray, self.mapReferencesTab)
		thisMap = max(potential.keys(), key=(lambda k: potential[k]))
		self.previousImageArray = self.currentImageArray
		self.currentImageArray = thisMapArray
		self.previousPotential = self.potential
		self.potential = potential
		self.thisMapPotential = potential[thisMap]
		
		if (potential[thisMap] > self.imageThreshold[view]):
			if (thisMap == "lijiang tower" and view == "Hero Select"):
				thisMap = self.getMap(screenImgArray, "Hero Select", True)
				potential = self.whatImageIsThis(thisMap, self.mapReferencesLijiang)
				thisMap = max(potential.keys(), key=(lambda k: potential[k]))
				thisMap = "lijiang-"+thisMap
			thisMapSplit = thisMap.split("-")
			if (self.currentMap[0] != thisMapSplit[0]):
				print("Map Changed")
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
		thisSide = self.teamFromPixel(pixelToCheck)
		print (thisSide)
		
		if (thisSide == "neither"):
			thisSide = self.previousMapSide
		
		if (thisSide != self.previousMapSide):
			self.previousMapSide = self.currentMapSide
			self.currentMapSide = thisSide
			return True
		else: 
			return False
			
	def teamFromPixel(self, pixelToCheck):
		red = pixelToCheck[0]
		green = pixelToCheck[1]
		blue = pixelToCheck[2]
		#print(red)
		#print(green)
		#print(blue)
		if ((red > 195) and (green < 200) and (blue < 200)):
			thisSide = "offense"
		elif ((red < 200) and (green > 180) and (blue > 100)):
			thisSide = "defense"
		else: 
			thisSide = "neither"
			#print ("rgb: " + str(red) + "," + str(green) + "," + str(blue))
		return thisSide
	
	def identifyObjectiveProgress(self, imgArray, mode="standard"):
		if (self.currentMap == [None] or self.objectiveProgress["gameOver"] == True):
			return False
		
		mapType = self.mapType()

		if (mapType == "transition"):
			#need to go from assault to escort
			if (self.objectiveProgress["currentType"] == None):
				self.objectiveProgress["currentType"] = "assault"
			placeholder = True
		
		if (mapType == "assault" or self.objectiveProgress["currentType"] == "assault"):
			newImageArray = self.identifyAssaultObjectiveProgress(imgArray, mapType, mode)

		if (mapType == "control" or self.objectiveProgress["currentType"] == "control"):
			newImageArray = self.identifyControlObjectiveProgress(imgArray, mode)
			
		if (mapType == "escort" or self.objectiveProgress["currentType"] == "escort"):
			newImageArray = self.identifyEscortObjectiveProgress(imgArray, mapType, mode)

		if (mode == "for_reference"):
			path = "Debug"
			#save image
			img = Image.fromarray(newImageArray)
			img.save(path+"\\Potential Objective.png", "PNG")
	
	def identifyAssaultObjectiveProgress(self, imgArray, mapType, mode="standard"):
		dimensions = {}
		
		#Assault Point 1
		dimensions["startX"] = 918
		dimensions["endX"] = 930
		dimensions["startY"] = 114
		dimensions["endY"] = 128
		#color for side
		pixelToCheck = imgArray[108][927]
		
		newImageArray = self.cutAndThreshold(imgArray, dimensions)
		potential = self.whatImageIsThis(newImageArray, self.assaultReference)
		thisStatus = max(potential.keys(), key=(lambda k: potential[k]))
		
		if (potential[thisStatus] > self.imageThreshold["Assault"]):  #max 166?
			#get current progress
			if (thisStatus == "Done"):
				if (mapType == "transition"):
					self.objectiveProgress["currentType"] = "escort"
				else:
					#Assault Point 2
					dimensions["startX"] = 994
					dimensions["endX"] = 1006
					dimensions["startY"] = 114
					dimensions["endY"] = 128
					pixelToCheck = imgArray[108][997]
					newImageArray = self.cutAndThreshold(imgArray, dimensions)
					potential = self.whatImageIsThis(newImageArray, self.assaultReference)
					thisStatus = max(potential.keys(), key=(lambda k: potential[k]))
					self.identifyAssaultPointProgress(imgArray, 1, mode)
			elif (thisStatus != "Locked"):
				self.identifyAssaultPointProgress(imgArray, 0, mode)
		elif (mapType == "transition"):
			dimensions["startX"] = 760
			dimensions["endX"] = 772
			dimensions["startY"] = 114
			dimensions["endY"] = 128
			newImageArray = self.cutAndThreshold(imgArray, dimensions)
			potential = self.whatImageIsThis(newImageArray, self.assaultReference)
			thisStatus = max(potential.keys(), key=(lambda k: potential[k]))
			if (potential[thisStatus] > self.imageThreshold["Assault"] and (thisStatus == "Locked" or thisStatus == "Done")):
				print("Transition to Escort")
				self.objectiveProgress["currentType"] = "escort"
			else:
				self.identifyGameEnd(imgArray, mode)
		else:
			self.identifyGameEnd(imgArray, mode)
			
		print(thisStatus)
		print(potential)
		if (thisStatus != "Locked"):
			thisSide = self.teamFromPixel(pixelToCheck)
			print(thisSide)
		return newImageArray
	
	def identifyAssaultPointProgress(self, imgArray, pointNumber, mode="standard"):
		assaultPercentComplete = 0
		for pixelCoordinates in self.assaultPixelsToCheck[pointNumber]:
			thisPixel = imgArray[pixelCoordinates[1]][pixelCoordinates[0]]
			avgColorBrightness = reduce(lambda x, y: int(x) + int(y), thisPixel[:3])/3
			if avgColorBrightness > 248:
				assaultPercentComplete = assaultPercentComplete + 1
			else:
				#print(pixelCoordinates)
				#print(thisPixel)
			
		print(assaultPercentComplete)
	
	def identifyControlObjectiveProgress(self, imgArray, mode="standard"):
		dimensions = {}
		
		dimensions["startX"] = 952
		dimensions["endX"] = 968
		dimensions["startY"] = 78
		dimensions["endY"] = 102
		pixelToCheck = {}
		pixelToCheck["current"] = imgArray[108][959]
		pixelToCheck["left"] = {}
		#pixelToCheck["left"][0] = imgArray[91][734] #what is this?
		pixelToCheck["left"][0] = imgArray[91][774]
		pixelToCheck["left"][1] = imgArray[91][814]
		pixelToCheck["right"] = {}
		pixelToCheck["right"][0] = imgArray[91][1146]
		pixelToCheck["right"][1] = imgArray[91][1106]#far right
		#pixelToCheck["right"][2] = imgArray[91][1186] # what is this?
		
		newImageArray = self.cutAndThreshold(imgArray, dimensions)
		potential = self.whatImageIsThis(newImageArray, self.controlReference)
		thisStatus = max(potential.keys(), key=(lambda k: potential[k]))
		
		#max 384, lower limit: 250
		if (potential[thisStatus] > self.imageThreshold["Control"]):
			print(thisStatus)
			print(potential)
			if (thisStatus != "Locked"):
				thisSide = self.teamFromPixel(pixelToCheck["current"])
				print("Current Controller: " + thisSide)
			for pixelIndex, thisPixel in pixelToCheck["left"].items():
				teamResult = self.teamFromPixel(thisPixel)
				if teamResult == "neither":
					print("Our Team Progress: " + str(pixelIndex))
					break
			for pixelIndex, thisPixel in pixelToCheck["right"].items():
				teamResult = self.teamFromPixel(thisPixel)
				if teamResult == "neither":
					print("Their Team Progress: " + str(pixelIndex))
					break
		else:
			self.identifyGameEnd(imgArray, mode)
		
		return newImageArray
	
	def identifyEscortObjectiveProgress(self, imgArray, mapType, mode="standard"):
		dimensions = {}
		
		if ("escortProgress" not in self.objectiveProgress):
			self.objectiveProgress["escortProgress"] = []
	
		if (mapType == "escort" and self.objectiveProgress["unlocked"] == False):
			#check for lock symbol
			dimensions["startX"] = 953
			dimensions["endX"] = 965
			dimensions["startY"] = 111
			dimensions["endY"] = 125
			
			newImageArray = self.cutAndThreshold(imgArray, dimensions)
			lockReference = {}
			lockReference["Locked"] = self.assaultReference["Locked"]
			potential = self.whatImageIsThis(newImageArray, lockReference)
			
			if (potential["Locked"] > self.imageThreshold["Assault"]):  #max 166?
				print("Locked")
				print(potential)
				if (mode == "for_reference"):
					path = "Debug"
					#save image
					img = Image.fromarray(newImageArray)
					img.save(path+"\\Potential Objective.png", "PNG")
				return
		dimensions["startX"] = 787
		dimensions["endX"] = 1135
		dimensions["startY"] = 118
		dimensions["endY"] = 128

		if (mapType == "transition"):
			dimensions["startX"] = 824
			dimensions["endX"] = 1172
		
		# dorodo point 1: 32%
		# dorodo point 2: 68%
		# route66 point 1: 34%
		# route66 point 2: 70%
		# watchpoint point 1: 33%
		# watchpoint point 2: 66%
		# eichenwalde point 1: 66%
		# eichenwalde point 1: 74% (Free move after door)
		# hollywood point 1: 61%
		# king's row point 1: 62%
		# numbani point 1: 58%
		
		newImageArray = self.cutImage(imgArray, dimensions)
		endFound = False
		for X in range(0, (dimensions["endX"]-dimensions["startX"])):
			
			pixelToCheck = newImageArray[5][X]
			pixelTeam = self.teamFromPixel(pixelToCheck)
			if (pixelTeam != self.currentMapSide):
				percentComplete = round((X)/(dimensions["endX"]-dimensions["startX"]) * 100)
				print("Percent Complete: " + str(percentComplete))
				endFound = True
				break
		
		if endFound == False:
			percentComplete = 100
			print("Percent Complete: 100 - Complete Color Change")
		
		escortProgressLength = len(self.objectiveProgress["escortProgress"])
		if (percentComplete > 0 or escortProgressLength > 0):
			self.objectiveProgress["escortProgress"].append(percentComplete)
		
		#check to see if we can confirm the match has started, unlocking the Escort Objective
		if escortProgressLength > 2:
			minimum = 101
			maximum = -1
			for thisEscortProgress in self.objectiveProgress["escortProgress"][-3:]: #last 3
				if thisEscortProgress > maximum:
					maximum = thisEscortProgress
				if thisEscortProgress < minimum: 
					minimum = thisEscortProgress
			if minimum != 0 and (maximum-minimum) < 5:
				self.objectiveProgress["unlocked"] = True
		
		if percentComplete == 0:
			self.identifyGameEnd(imgArray, mode)
	
	def identifyGameEnd(self, imgArray, mode="standard"):
		dimensions = {}
		dimensions["startX"] = 643
		dimensions["endX"] = 1305
		dimensions["startY"] = 440
		dimensions["endY"] = 633
		croppedImageArray = self.cutImage(imgArray, dimensions)
		# -- Check for Victory  -- #
		#convert to black and white based on yellow
		yellow = [230, 205, 100]
		result = self.gameEndFormatImage(croppedImageArray, yellow, "Victory")
		if (type(result) is not bool):
			referenceDictionary = {}
			referenceDictionary["Victory"] = self.gameEndReference["Victory"]
			potential = self.whatImageIsThis(np.asarray(result), referenceDictionary)
			pprint(potential)
			if potential["Victory"] > self.imageThreshold["Victory"]:
				self.objectiveProgress["gameEnd"] = "Victory"
				print("Victory!")
				self.submitStatsAndClear();
		if self.objectiveProgress["gameEnd"] != "Victory":
			# -- Check for Defeat -- #
			red = [210, 120, 130]
			result = self.gameEndFormatImage(croppedImageArray, red, "Defeat")
			if (type(result) is not bool):
				referenceDictionary = {}
				referenceDictionary["Defeat"] = self.gameEndReference["Defeat"]
				potential = self.whatImageIsThis(np.asarray(result), referenceDictionary)
				pprint(potential)
				if potential["Defeat"] > self.imageThreshold["Defeat"]: #max 7200
					self.objectiveProgress["gameEnd"] = "Defeat"
					print("Defeat! :(")
					self.submitStatsAndClear();
		if (type(result) is not bool and mode == "for_reference"):
			path = "Debug"
			#save image
			#img = Image.fromarray(newCroppedImageArray)
			result.save(path+"\\Game End.png", "PNG")
	
	def gameEndFormatImage(self, imageArray, color, mode):
		croppedImageArray = imageArray.copy()
		croppedImageArray.setflags(write=1)
		
		img = Image.fromarray(croppedImageArray)
		croppedImageArray = np.asarray((img.resize((200,56), Image.BILINEAR )))
		croppedImageArray.setflags(write=1)
		
		blackCheckColumn = {}
		rowsToCut = []
		columnsToCut =  []
		croppedImageArrayLength = len(croppedImageArray)-1
		
		for rowNumber,eachRow in enumerate(croppedImageArray):
			blackCheckRow = True
			
			for pixelNumber,eachPixel in enumerate(eachRow):
				
				if rowNumber == 0:
					blackCheckColumn[pixelNumber] = True
				
				goWhite = False
				if mode == "Victory":
					if ((eachPixel[0] > color[0]) and (eachPixel[1] > color[1]) and (eachPixel[2] < color[2])): # greater, greater, less
						goWhite = True
				elif mode == "Defeat":
					if ((eachPixel[0] > color[0]) and (eachPixel[1] < color[1]) and (eachPixel[2] < color[2])): # greater, less, less
						goWhite = True
				if goWhite:
					croppedImageArray[rowNumber][pixelNumber] = [255,255,255] #White
					blackCheckRow = False
					blackCheckColumn[pixelNumber] = False
				else: 
					croppedImageArray[rowNumber][pixelNumber] = [0,0,0] #Black
				#crop box where entire column is black
				
				if (rowNumber == croppedImageArrayLength and blackCheckColumn[pixelNumber] == True):
					columnsToCut.append(pixelNumber)
			#crop box where entire row is black
			if blackCheckRow == True:
				rowsToCut.append(rowNumber)
		
		newDimensions = {}
		#cut top edge
		for index, thisRow in enumerate(rowsToCut):
			if  index != 0:
				if (previousRow + 1 != thisRow):
					newDimensions["startY"] = previousRow
					break
			previousRow = thisRow
		#cut bottom edge
		for index, thisRow in enumerate(reversed(rowsToCut)):
			if  index != 0:
				if (previousRow - 1 != thisRow):
					newDimensions["endY"] = previousRow
					break
			previousRow = thisRow
		#far left  --  Only crop far left and right, not between letters
		for index, thisColumn in enumerate(columnsToCut):
			if  index != 0:
				if (previousColumn + 1 != thisColumn):
					newDimensions["startX"] = previousColumn
					break
			previousColumn = thisColumn
		#far right
		for index, thisColumn in enumerate(reversed(columnsToCut)):
			if  index != 0:
				if (previousColumn - 1 != thisColumn):
					newDimensions["endX"] = previousColumn
					break
			previousColumn = thisColumn
		if (("startY" not in newDimensions) or ("endY" not in newDimensions) or ("startX" not in newDimensions) or ("endX" not in newDimensions)):
			path = "Debug"
			#save image
			img = Image.fromarray(croppedImageArray)
			img.save(path+"\\" + mode + ".png", "PNG")
			return False
		newCroppedImageArray = self.cutImage(croppedImageArray, newDimensions)
		img = Image.fromarray(newCroppedImageArray)
		resizedImageArray = self.threshold(np.asarray((img.resize((160,45), Image.BILINEAR ))))
		resizedImage = Image.fromarray(resizedImageArray)
		
		if(len(resizedImageArray[0]) * len(resizedImageArray) != len(self.gameEndReference["Victory"][0])):
			return False
		else:
			return resizedImage
	
	def cutImage(self, imgArray, dimensions):
		mapImage = imgArray[dimensions["startY"]:dimensions["endY"], dimensions["startX"]:dimensions["endX"]]
		mapImageArray = np.asarray(mapImage)
		return mapImageArray
	
	def cutAndThreshold(self, imgArray, dimensions):
		mapImageArray = self.cutImage(imgArray, dimensions)
		return self.threshold(mapImageArray)
	
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
			
	def submitStatsAndClear(self):
		self.objectiveProgress["gameOver"] = True
		print ("Sumbit Stats and Clear")
			
			