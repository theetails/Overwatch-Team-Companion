from functools import reduce
from collections import Counter

class GameObject:
	
	def readReferences(self, filename):
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
	
	def threshold(self, imageArray):
		balanceArray = []
		newArray = imageArray.copy()
		newArray.setflags(write=1)
		
		#calculate mean (balance)
		for eachRow in imageArray:
			for eachPixel in eachRow:
				avgNum = reduce(lambda x, y: int(x) + int(y), eachPixel[:3])/3
				balanceArray.append(avgNum)
		balance = reduce(lambda x, y: x + y, balanceArray)/len(balanceArray)
		
		newArray = self.imageToBlackAndWhite(newArray, balance)
		return newArray
	
	def imageToBlackAndWhite(self, imageArray, cutOff):
		for rowNumber,eachRow in enumerate(imageArray):
			for pixelNumber,eachPixel in enumerate(eachRow):
				if reduce(lambda x, y: int(x) + int(y), eachPixel[:3])/3 > cutOff:
					imageArray[rowNumber][pixelNumber] = [255,255,255] #White
				else: 
					imageArray[rowNumber][pixelNumber] = [0,0,0] #Black
		return imageArray
	
	def whatImageIsThis(self, capturedImage, referenceImagesDictionary):
		matchedArray = []
		capturedImageList = capturedImage.tolist()
		capturedImageString = str(capturedImageList)
		capturedImagePixels = capturedImageString.split('],')
		
		for itemName, referenceImages in referenceImagesDictionary.items():
			x = 0
			for referencePixels in referenceImages:
				while x < len(referencePixels):
					#for referencePixel in referenceImage:
					#print("Reference Pixel: "+referencePixels[x]+" "+"Captured Pixel: "+capturedImagePixels[x])
					if referencePixels[x]==capturedImagePixels[x]:
						matchedArray.append(itemName)
					x += 1
		count = Counter(matchedArray)
		return count
		
	