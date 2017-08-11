from functools import reduce
from collections import Counter
import re


class GameObject:
    @staticmethod
    def read_references(filename):
        regex = re.compile('\d+')
        reference_image_file = open(filename, 'r').read()
        reference_image_file = reference_image_file.split('\n')
        reference_image_dictionary = {}
        for reference_image in reference_image_file:
            if len(reference_image) > 1:
                image_string = reference_image.split('::')  # 0 is name, 1 is pixel arrays
                if image_string[0] not in reference_image_dictionary:
                    reference_image_dictionary[image_string[0]] = []
                row_list = image_string[1].split('],')
                for row in row_list:
                    reference_image_dictionary[image_string[0]].append([])
                    pixel_list = regex.findall(row)
                    final_pixel_list = []
                    for pixel in pixel_list:
                        final_pixel_list.append(int(pixel))
                    reference_image_dictionary[image_string[0]][-1] = final_pixel_list
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
        for each_row in image_array:
            for each_pixel in each_row:
                avg_num = reduce(lambda x, y: int(x) + int(y), each_pixel[:3]) / 3
                balance_array.append(avg_num)
        balance = reduce(lambda x, y: x + y, balance_array) / len(balance_array)
        return balance

    @staticmethod
    def image_to_black_and_white(image_array, cut_off):
        new_array = image_array.copy()
        new_array.setflags(write=1)
        for row_number, each_row in enumerate(new_array):
            for pixel_number, each_pixel in enumerate(each_row):
                if reduce(lambda x, y: int(x) + int(y), each_pixel[:3]) / 3 > cut_off:
                    new_array[row_number][pixel_number] = [255, 255, 255]  # White
                else:
                    new_array[row_number][pixel_number] = [0, 0, 0]  # Black
        return new_array

    @staticmethod
    def what_image_is_this(captured_image, reference_images_dictionary):
        matched_array = []
        captured_image_list = captured_image.tolist()
        # captured_image_string = str(captured_image_list)
        # captured_image_pixels = captured_image_string.split('],')

        for item_name, reference_image in reference_images_dictionary.items():
            row = 0
            for reference_row in reference_image:
                pixel = 0
                for reference_pixel in reference_row:
                    # print("Reference Pixel: " + str(reference_pixel) +
                        # " Captured Pixel: " + str(captured_image_list[row][pixel][0]))
                    if reference_pixel == captured_image_list[row][pixel][0]:
                        matched_array.append(item_name)
                    pixel = pixel + 1
                row = row + 1
        count = Counter(matched_array)
        return count
