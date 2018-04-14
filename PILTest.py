from PIL import Image, ImageFilter, ImageOps
from scipy.misc import imresize
from scipy.ndimage.filters import gaussian_filter

import numpy as np

from GameObject import GameObject


class PILTest:

    @staticmethod
    def main():
        go = GameObject()
        map_image = Image.open('Debug\\Full Original Map.png')

        blur = map_image.filter(ImageFilter.BLUR)
        blur.save("Debug\\Filter-Blur.png", "PNG")

        contour = map_image.filter(ImageFilter.CONTOUR)
        contour.save("Debug\\Filter-Contour.png", "PNG")

        detail = map_image.filter(ImageFilter.DETAIL)
        detail.save("Debug\\Filter-Detail.png", "PNG")

        edge_enhance = map_image.filter(ImageFilter.EDGE_ENHANCE)
        edge_enhance.save("Debug\\Filter-EE.png", "PNG")

        edge_enhance_more = map_image.filter(ImageFilter.EDGE_ENHANCE_MORE)
        edge_enhance_more.save("Debug\\Filter-EEM.png", "PNG")

        emboss = map_image.filter(ImageFilter.EMBOSS)
        emboss.save("Debug\\Filter-Emboss.png", "PNG")

        find_edges = map_image.filter(ImageFilter.FIND_EDGES)
        find_edges.save("Debug\\Filter-FindEdges.png", "PNG")

        smooth = map_image.filter(ImageFilter.SMOOTH)
        smooth.save("Debug\\Filter-Smooth.png", "PNG")

        smooth_more = map_image.filter(ImageFilter.SMOOTH_MORE)
        smooth_more.save("Debug\\Filter-SmoothMore.png", "PNG")

        sharpen = map_image.filter(ImageFilter.SHARPEN)
        sharpen.save("Debug\\Filter-Sharpen.png", "PNG")

        eem_then_find_edges = edge_enhance_more.filter(ImageFilter.FIND_EDGES)
        eem_then_find_edges.save("Debug\\Filter-EEM-FindEdges.png", "PNG")

        eem_then_find_edges_smooth = eem_then_find_edges.filter(ImageFilter.SMOOTH_MORE)
        eem_then_find_edges_smooth.save("Debug\\Filter-EEM-FindEdges-Smooth.png", "PNG")

        eem_2 = edge_enhance_more.filter(ImageFilter.SMOOTH_MORE).filter(ImageFilter.EDGE_ENHANCE_MORE)
        eem_2 = eem_2.filter(ImageFilter.SMOOTH_MORE).filter(ImageFilter.EDGE_ENHANCE_MORE)
        eem_2.save("Debug\\Filter-EEM2.png", "PNG")

        find_edges_smooth = find_edges.filter(ImageFilter.SMOOTH_MORE)
        find_edges_smooth.save("Debug\\Filter-FindEdges-Smooth.png", "PNG")

        img_array = ImageOps.invert(contour)
        # img_array = np.asarray(find_edges_smooth)
        img_array = np.asarray(img_array)

        img_array.setflags(write=True)
        for row_number, row in enumerate(img_array):
            for column_number, column in enumerate(row):
                first_four_rows = list(range(0, 1))
                last_four_rows = list(range(len(img_array)-1, len(img_array)))
                if row_number in first_four_rows or row_number in last_four_rows:
                    # print(row_number)
                    # print(column_number)
                    # print(img_array[row_number][column_number])
                    img_array[row_number][column_number] = [0, 0, 0]
                elif column_number == 0 or column_number == len(column):
                    img_array[row_number][column_number] = [0, 0, 0]

        blurred_image_array = gaussian_filter(img_array, 1)
        scaled_image_array = imresize(img_array, (19, 180))
        Image.fromarray(scaled_image_array).save("Debug\\Threshold-Before.png", "PNG")
        threshold = go.threshold(scaled_image_array)

        img = Image.fromarray(threshold)
        img.save("Debug\\Threshold.png", "PNG")



test = PILTest()
test.main()
