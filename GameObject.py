from functools import reduce
from collections import Counter


class GameObject:
    @staticmethod
    def read_references(filename):
        reference_image_file = open(filename, 'r').read()
        reference_image_file = reference_image_file.split('\n')
        reference_image_dictionary = dict()
        for referenceImage in reference_image_file:
            if len(referenceImage) > 1:
                image_string = referenceImage.split('::')  # 0 is name, 1 is pixel arrays
                if image_string[0] not in reference_image_dictionary:
                    reference_image_dictionary[image_string[0]] = []
                split_string = image_string[1].split('],')
                reference_image_dictionary[image_string[0]].append(split_string)
        return reference_image_dictionary

    def threshold(self, image_array):
        balance = self.get_image_balance(image_array)

        # ("Balance: " + str(balance))
        # if 240 < balance < 252:
        #     balance = 252
        new_array = self.image_to_black_and_white(image_array, balance)
        return new_array

    @staticmethod
    def get_image_balance(image_array):
        balance_array = []
        for eachRow in image_array:
            for eachPixel in eachRow:
                avg_num = reduce(lambda x, y: int(x) + int(y), eachPixel[:3]) / 3
                balance_array.append(avg_num)
        balance = reduce(lambda x, y: x + y, balance_array) / len(balance_array)
        return balance

    @staticmethod
    def image_to_black_and_white(image_array, cut_off):
        new_array = image_array.copy()
        new_array.setflags(write=1)
        for rowNumber, eachRow in enumerate(new_array):
            for pixelNumber, eachPixel in enumerate(eachRow):
                if reduce(lambda x, y: int(x) + int(y), eachPixel[:3]) / 3 > cut_off:
                    new_array[rowNumber][pixelNumber] = [255, 255, 255]  # White
                else:
                    new_array[rowNumber][pixelNumber] = [0, 0, 0]  # Black
        return new_array

    @staticmethod
    def what_image_is_this(captured_image, reference_images_dictionary):
        matched_array = []
        captured_image_list = captured_image.tolist()
        captured_image_string = str(captured_image_list)
        captured_image_pixels = captured_image_string.split('],')

        for itemName, reference_images in reference_images_dictionary.items():
            x = 0
            for referencePixels in reference_images:
                while x < len(referencePixels):
                    # for referencePixel in referenceImage:
                    # print("Reference Pixel: "+referencePixels[x]+" "+"Captured Pixel: "+captured_image_pixels[x])
                    if referencePixels[x] == captured_image_pixels[x]:
                        matched_array.append(itemName)
                    x += 1
        count = Counter(matched_array)
        return count
