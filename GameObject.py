from functools import reduce
from collections import Counter
import re
import numpy as np
from PIL import Image


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
        """ Turns an image to black and white based on the median brightness

        :param image_array: Numpy Array of image
        :return: Numpy Array of processed image
        """
        balance = self.get_image_balance(image_array)
        new_array = self.image_to_black_and_white(image_array, balance)
        return new_array

    @staticmethod
    def get_image_balance(image_array):
        """ Calculates the median brightness of an image

        :param image_array: Numpy Array of image
        :return: Int of median brightness (0-255)
        """
        balance_array = []
        for each_row in image_array:
            for each_pixel in each_row:
                avg_num = reduce(lambda x, y: int(x) + int(y), each_pixel[:3]) / 3
                balance_array.append(avg_num)
        balance = reduce(lambda x, y: x + y, balance_array) / len(balance_array)
        return balance

    @staticmethod
    def image_to_black_and_white(image_array, cut_off):
        """ Calculates the median brightness of an image

        :param image_array: Numpy Array of image
        :param cut_off: Int of median brightness (0-255)
        :return: Numpy Array of black and white image
        """
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
        """ Compares the captured image to the saved reference images and ranks how similar they are

        :param captured_image: Numpy Array of image in question
        :param reference_images_dictionary: Dictionary of images (lists) to compare to
        :return: Dictionary of the scores of the comparisons (0 - 1)
        """
        matched_array = []
        captured_image_list = captured_image.tolist()
        total = {}

        for item_name, reference_image in reference_images_dictionary.items():
            total[item_name] = 0
            row = 0
            for reference_row in reference_image:  # captured_image must not be larger than any reference image
                pixel = 0
                for reference_pixel in reference_row:
                    total[item_name] += 1
                    # print("Reference Pixel: " + str(reference_pixel) +
                    #     " Captured Pixel: " + str(captured_image_list[row][pixel][0]))
                    if reference_pixel == captured_image_list[row][pixel][0]:
                        matched_array.append(item_name)
                    pixel = pixel + 1
                row = row + 1
        counter = Counter(matched_array)
        most_common = counter.most_common()
        ratios = {}
        for item in most_common:
            ratios[item[0]] = item[1] / total[item[0]]
        return ratios

    def what_word_is_this(self, captured_image, encoded_reference_images_dictionary, letter_string="", loop_count=0):
        """ Work in Progress
        """
        # print("what_word_is_this")
        if loop_count == 0:
            # flipped = np.flipud(captured_image)
            # flipped.setflags(write=True)
            # for row_number, row in enumerate(flipped):
            #     left_shift = int(row_number / 3.72)  # 41 / 11
            #     if left_shift > 0:
            #         for column_number, pixel in enumerate(row):
            #             try:
            #                 flipped[row_number][column_number] = flipped[row_number][column_number + left_shift]
            #             except IndexError:
            #                 flipped[row_number][column_number] = 0
            # captured_image = np.flipud(flipped)
            # save
            img = Image.fromarray(captured_image)
            img.save("Debug\\Full.png", "PNG")
        try:
            # desired_loop = 121  # 91: O 121 : E
            # if loop_count < desired_loop:
            #     sliced_image = np.delete(captured_image, 0, axis=1)
            #     return self.what_word_is_this(sliced_image, encoded_reference_images_dictionary,
            #                                   letter_string=letter_string, loop_count=loop_count + 1)
            # if loop_count == desired_loop + 1:
            #     return letter_string

            captured_image_list = captured_image.tolist()
            all_black = True
            for row in captured_image_list:
                if len(row) == 1:
                    return letter_string
                if row[1][0] == 255:
                    all_black = False
            if all_black:
                sliced_image = np.delete(captured_image, 0, axis=1)
                if sliced_image.size != 0:
                    return self.what_word_is_this(sliced_image, encoded_reference_images_dictionary,
                                                  letter_string=letter_string, loop_count=loop_count + 1)
                else:
                    return letter_string

            equivalent_columns = np.all(captured_image == captured_image[0, :], axis=0)
            # print(equivalent_columns)
            next_all_black = None
            for index, pixel in enumerate(equivalent_columns):
                if index > 0 and next_all_black != 0:
                    if pixel[0]:
                        next_all_black = index
                        break
            if next_all_black is None:
                next_all_black = 0
            # print("next_all_black: " + str(index))
            range_to_remove = list(range(next_all_black + 1, len(captured_image_list[0])))
            # print("range_to_remove: " + str(range_to_remove))
            sliced_image = np.delete(captured_image, range_to_remove, axis=1)
            img = Image.fromarray(sliced_image)
            img.save("Debug\\" + str(loop_count) + " Letter " + ".png", "PNG")

            encoded_captured_image = self.run_length_encode(sliced_image.tolist(), pixel_array=True)
            potential = self.what_letter_is_this(encoded_captured_image, encoded_reference_images_dictionary)

            max_potential = max(potential.keys(), key=(lambda k: potential[k]))

            print(str(loop_count) + ": " + str(max_potential) + " " + str(round(potential[max_potential], 2)))
            # print(potential)
            # save
            img = Image.fromarray(captured_image)
            img.save("Debug\\" + str(loop_count) + " Letter " + str(max_potential) + " " +
                     str(round(potential[max_potential], 2)) + ".png", "PNG")

            if potential[max_potential] <= 1:
                sliced_image = np.delete(captured_image, 0, axis=1)
                if sliced_image.size != 0:
                    return self.what_word_is_this(sliced_image, encoded_reference_images_dictionary,
                                                  letter_string=letter_string, loop_count=loop_count + 1)
                else:
                    return letter_string
            else:
                # print(str(loop_count) + ": " + str(max_potential) + " " + str(potential[max_potential]))
                # print(potential)
                letter_string = letter_string + max_potential
                sliced_image = np.delete(
                    captured_image, range(0, encoded_reference_images_dictionary[max_potential]["width"]-1), axis=1)

                # # save
                # img = Image.fromarray(captured_image)
                # img.save("Debug\\" + str(loop_count) + " Letter " + str(max_potential) + ".png", "PNG")

                if sliced_image.size > 19 * 6:
                    return self.what_word_is_this(sliced_image, encoded_reference_images_dictionary,
                                                  letter_string=letter_string,
                                                  loop_count=loop_count + 1)
                else:
                    return letter_string
        except Exception as exception:
            print(exception)

    def what_letter_is_this(self, captured_image_list, reference_images_dictionary):
        """ Work in Progress
        """

        print("what letter is this")
        matched_array = []
        # captured_image_list = captured_image.tolist()
        # captured_image_string = str(captured_image_list)
        # captured_image_pixels = captured_image_string.split('],')

        total_potential = {}
        total_score = {}
        for item_name, reference_image in reference_images_dictionary.items():
            # if item_name not in ["e", "l"]:
            #     continue
            # print(item_name)
            total_potential[item_name] = 0
            total_score[item_name] = 0
            width = reference_image["width"]
            for row_number, reference_row in enumerate(reference_image["image"]):
                # print("row_number: " + str(row_number))
                potential, score = self.score_row(captured_image_list["image"][row_number], reference_row, width)
                total_potential[item_name] += potential
                total_score[item_name] += score
        print("total score")
        print(total_score)
        counter = Counter(total_score)
        # print(counter)
        most_common = counter.most_common()
        # print(most_common)
        ratios = {}
        for item in most_common:
            ratios[item[0]] = item[1] / total_potential[item[0]]
        # print(ratios)
        return ratios

    @staticmethod
    def score_row(captured_row, reference_row, width):
        """ Work in Progress
        """
        print_row = False
        if print_row:
            print(captured_row)
            print(reference_row)
        row_score = 0
        if reference_row:
            concurrent_captured_segments = []
            for reference_segment in reference_row:
                segment_score = 0
                if print_row:
                    print('segment ' + str(reference_segment))
                reference_segment_list = list(range(reference_segment[0], reference_segment[1]+1))
                for index, captured_segment in enumerate(captured_row):
                    if captured_segment[0] > reference_segment[1]:
                        break
                    captured_segment_list = list(range(captured_segment[0], captured_segment[1]+1))
                    concurrent_pixels = set(reference_segment_list).intersection(captured_segment_list)
                    if not concurrent_pixels:
                        continue
                    concurrent_captured_segments.append(index)

                    longest_segment = len(range(
                        min(reference_segment[0], captured_segment[0]),
                        max(reference_segment[1], captured_segment[1]) + 1
                    ))
                    # longest_segment = max([len(reference_segment_list), len(captured_segment_list)])
                    segment_difference = longest_segment - len(concurrent_pixels)
                    segment_score += 3 - segment_difference

                    if print_row:
                        print('comparison')
                        print('concurrent_captured_segments: ' + str(concurrent_captured_segments))
                        print(concurrent_pixels)
                        print("segment_difference: " + str(segment_difference))
                        print("segment_score: " + str(segment_score))
                row_score += segment_score
            unique_concurrent_captured_segments = set(concurrent_captured_segments)
            number_of_unique_concurrent_captured_segments = len(unique_concurrent_captured_segments)
            for index, captured_segment in enumerate(captured_row):
                if captured_segment[0] < width and index not in unique_concurrent_captured_segments:
                    if print_row:
                        print("missing segment: " + str(captured_segment))
                    row_score = -15
            if print_row:
                print(concurrent_captured_segments)
                print("segment count: " + str(len(reference_row)) + " " + str(number_of_unique_concurrent_captured_segments))
            if len(reference_row) != number_of_unique_concurrent_captured_segments:
                row_score = -5
        if print_row:
            print("row score " + str(row_score))
        return 1, row_score

    @staticmethod
    def run_length_encode(image, pixel_array=False):
        """ Work in Progress
        """
        # print(image)
        encoded_image = []
        width = len(image[1])
        for row in image:
            encoded_row = []
            for pixel_number, pixel in enumerate(row):
                # print(pixel)
                if pixel_array:
                    pixel = pixel[0]
                if pixel == 255:
                    if not encoded_row:
                        encoded_row.append([pixel_number, pixel_number])
                    elif encoded_row[-1][1] == pixel_number - 1:
                        encoded_row[-1][1] = pixel_number
                    else:
                        encoded_row.append([pixel_number, pixel_number])
            encoded_image.append(encoded_row)
        return {
            "width": width,
            "image": encoded_image
        }
