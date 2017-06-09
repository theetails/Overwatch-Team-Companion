from PIL import Image
import numpy as np
from scipy.misc import imresize
import operator
import subprocess as sp
from functools import reduce
from datetime import datetime, timedelta
from pprint import pprint #temporary for debugging

from GameObject import GameObject

class TimeInfo(GameObject):
	
	def __init__(self, debugMode):
		self.debugMode = debugMode
		self.setDigitDimensions()
		self.resetTime()
	
	def resetTime(self):
		self.elapsedTime = datetime.min
		self.mapStartTime = None
	
	def setDigitDimensions(self):
		self.digitReferences = self.readReferences("Reference\\DigitImageList.txt")
		self.colonReference = self.readReferences("Reference\\ColonImageList.txt")
	
		digitDimensions = {}
		digitDimensions["startX"] = 154
		digitDimensions["endX"] = 162
		digitDimensions["startY"] = 74
		digitDimensions["endY"] = 86
		
		self.digitDimensions = digitDimensions
		#1 pixels between; colon is 3 wide
		

	
	def main(self, screenImageArray):
		self.identifyTime(screenImageArray)
		
		return True
	
	def identifyTime(self, imgArray):
		colonFound = False
		digitsBeforeColon = 0
		digitsAfterColon = 0
		
		digitRequirement = 79 #Don't need? If its not a colon, it must be a digit
		colonRequirement = 33
		
		dimensions = self.digitDimensions.copy()
		loopCount = 0
		timeString = ""
		while True:
			if digitsBeforeColon > 0 and colonFound == False:
				colonDimensions = dimensions.copy()
				colonDimensions["endX"] = colonDimensions["endX"] - 5
				thisDigitArray = self.cutAndThreshold(imgArray, colonDimensions)
				potential = self.whatImageIsThis(thisDigitArray, self.colonReference)
				#print("Colon?")
				#print(potential)
				if potential["colon"] > colonRequirement:
					#print("Colon!")
					timeString = timeString + ":"
					colonFound = True
					dimensions["startX"] = dimensions["startX"] + 4
					dimensions["endX"] = dimensions["endX"] + 4
					self.saveDebugData(thisDigitArray, loopCount)
					loopCount = loopCount + 1
					continue
			thisDigitArray = self.cutAndThreshold(imgArray, dimensions)
			potential = self.whatImageIsThis(thisDigitArray, self.digitReferences)
			thisDigitFull = max(potential.keys(), key=(lambda k: potential[k]))
			thisDigitSplit = thisDigitFull.split("-")
			thisDigit = thisDigitSplit[0]
			
			if (thisDigit == "3" or thisDigit == "6" or thisDigit == "8"):
				if thisDigitArray[6][2][0] == 0:
					thisDigit = "3"
				elif thisDigitArray[4][6][0] == 0:
					thisDigit = "6"
				else: thisDigit = "8"
			
			#print (thisDigit)
			#print (potential)
			timeString = timeString + str(thisDigit)
			timeStringSplit = timeString.split(":")
			
			if colonFound == True:
				digitsAfterColon = digitsAfterColon + 1
			else: 
				digitsBeforeColon = digitsBeforeColon + 1
			
			self.saveDebugData(thisDigitArray, loopCount)
			if digitsAfterColon == 2:
				break
			dimensions["startX"] = dimensions["startX"] + 9
			dimensions["endX"] = dimensions["endX"] + 9
			loopCount = loopCount + 1
		
		thisTime = datetime.strptime(timeString, "%M:%S")
		thisTimeSeconds = int(timeStringSplit[1])
		thisTimeMinutes = int(timeStringSplit[0])
		thisTimeDelta = timedelta( minutes = thisTimeMinutes, seconds = thisTimeSeconds)
		print (datetime.strftime(thisTime, "%M:%S"))
		if self.mapStartTime == None: # and time > 0:00
			self.mapStartTime = datetime.now()-thisTimeDelta
			print (datetime.strftime(self.mapStartTime, "%H:%M:%S"))
		self.elapsedTime = thisTime
		
		#check to see if the times line up??
			#does a replay show the current game time? probably
	
	def cutImage(self, imgArray, dimensions):
		mapImage = imgArray[dimensions["startY"]:dimensions["endY"], dimensions["startX"]:dimensions["endX"]]
		mapImageArray = np.asarray(mapImage)
		return mapImageArray
	
	def cutAndThreshold(self, imgArray, dimensions):
		mapImageArray = self.cutImage(imgArray, dimensions)
		return self.threshold(mapImageArray)		
		
	def saveDebugData(self, imgArray, loopCount):
		path = "Debug"
		
		#save image
		img = Image.fromarray(imgArray)
		img.save(path+"\\Digit " + str(loopCount) + ".png", "PNG")
		'''
		if (currentTime != "for_reference"):
			#save potential
			debugFile = open(path+"\\Potential " + currentTime + " map.txt",'w')
			for potentialMap, value in sorted(self.potential.items(), key = operator.itemgetter(1), reverse = True):
				lineToWrite = str(value)+': '+potentialMap+'\n'
				debugFile.write(lineToWrite)
		'''
			