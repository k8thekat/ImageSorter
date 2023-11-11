from PIL.Image import Image as IMG
from PIL.Image import Resampling
from PIL import ImageFilter
import time
from typing import Union


class Image_Comparison:
    def __init__(self) -> None:
        self._match_percent: int = 90  # This is a percentage base match, results must be this or higher.
        self._line_detect: int = 128  # This is the 0-255 value we use to determine if the pixel is a "line"
        self._sample_percent: int = 10  # This is the % of edge cords to use for comparsion.

    @property
    def results(self) -> str:
        """
        Get the recent results from `compare()` showing the time taken and the percentage of a match.

        Returns:
            str: Results of recent compare
        """
        return f"Time taken {'{:.2f}'.format(self._etime)} seconds, with a {self._p_match}% match."

    def set_match_percent(self, percent: int = 90) -> None:
        """
        Sets the percentage required of match's to be considered a duplicate.


        Args:
            percent (int): 0-100 Percent value. Defaults to 80.

        Raises:
            ValueError: Value out of bounds.
        """
        if percent > 100 or percent < 0:
            raise ValueError("You must provide a value no greater than 100 and no less than 0.")
        self._match_percent = percent

    def set_line_detect(self, line_value: int = 128) -> None:
        """
        Sets the value to consider a "pixel" value to be considered a edge/line.


        Args:
            line_value (int): 0-255 Pixel value. Defaults to 128.

        Raises:
            ValueError: Value out of bounds.
        """
        if line_value > 255 or line_value < 0:
            raise ValueError("You must provide a value no greater than 255 and no less than 0.")
        self._line_detect = line_value

    def set_sample_percent(self, percent: int = 10) -> None:
        """
        Sets the percentage of Edge (X,Y) cords to use when comparing images. Images will have 10000+/- edges found.\n
        eg. `(10000 * .01) = 100` points checked.

        Args:
            percent (float, optional): 0-1 Percent value. Defaults to .01.

        Raises:
            ValueError: Value out of bounds.
        """
        if percent > 100 or percent < 0:
            raise ValueError("You must provide a value no greater than 100 and no less than 0.")
        self._sample_percent = percent

    def _convert(self, image: IMG) -> IMG:
        """
        Convert's the image to Grayscale `("L")` mode.

        Args:
            image (IMG): PIL Image

        Returns:
            IMG: PIL Image
        """
        if image.mode != "L":
            return image.convert("L")
        return image

    def _filter(self, image: IMG, filter=ImageFilter.FIND_EDGES) -> IMG:
        """
        Apply's the filter provided to the image and returns the results.


        Args:
            image (IMG): PIL Image
            filter (_type_, optional): PIL Image Filter. Defaults to ImageFilter.FIND_EDGES.

        Returns:
            IMG: _description_
        """
        return image.filter(filter=filter)

    def _image_resize(self, source: IMG, comparison: IMG, sampling=Resampling.BICUBIC, scale_percent: int = 50) -> tuple[IMG, IMG]:
        """
        Resizes the source image and resizes the comparison image to the same resolution as the source.\n
        `**THIS MUST BE RUN AFTER _filter**`

        Args:
            source (IMG): PIL Image
            comparison (IMG): PIL Image, the image to scale down.
            sampling (_type_, optional): PIL Resampling. Defaults to Resampling.BICUBIC.
            scale_percent (int, optional): The percentage to resize the image. Defaults to 50.

        Returns:
            tuple[IMG, IMG]: Resized PIL Images
        """

        dimensions: tuple[int, int] = (int(source.height * (scale_percent / 100)), int(source.width * (scale_percent / 100)))
        source = source.resize((dimensions[0], dimensions[1]), resample=sampling)
        comparison = comparison.resize((dimensions[0], dimensions[1]), resample=sampling)
        return source, comparison

    def _edge_detect(self, image: IMG) -> Union[None, list[tuple[int, int]]]:
        """
        Iterates from 0,0 looking for a pixel value above or equl to our `_line_detect` value. 

        When a pixel value high enough has been found it is added to our array.

        Args:
            image (IMG): PIL Image

        Returns:
            list(tuple(int, int)): List of (X,Y) cords.
        """
        edges: list[tuple[int, int]] = []
        for y in range(0, image.height):
            for x in range(0, image.width):
                pixel: int = image.getpixel((x, y))
                if pixel >= self._line_detect:
                    edges.append((x, y))

        return edges

    def _pixel_comparison(self, image: IMG, cords: tuple[int, int]) -> bool:
        """
        Uses (X,Y) cords to check a pixel if its above or equl to our `_line_detect` value. 

        If not; calls `_pixel_nearmatch`.

        Args:
            image (IMG): PIL Image
            cords (tuple[int, int]): X,Y cordinates.

        Returns:
            bool: True if the pixel value is higher than our `_line_detect` value else False.
        """
        if cords[0] > image.width or cords[0] < 0:
            raise ValueError(f"You provided a X value that is out of bounds. Value: {cords[0]} - Limit: {image.width}")
        if cords[1] > image.height or cords[1] < 0:
            raise ValueError(f"You provided a Y value that is out of bounds. Value: {cords[1]} - Limit: {image.height}")
        res: int = image.getpixel(cords)
        if isinstance(res, int):
            if res >= self._line_detect:
                return True

        return False

    def _pixel_nearmatch(self, image: IMG, cords: tuple[int, int], distance: int = 3) -> bool:
        """
        Will search a radius around (X,Y) cords based upon the provided distance value looking for a pixel value above our `_line_detect` value.

        Args:
            image (IMG): PIL Image
            cords (tuple[int, int]): X,Y cordinates.
            distance (int, optional): Radius from (X,Y). Defaults to 3.

        Returns:
            bool: True if the pixel value is higher than our `_line_detect` value else False.
        """
        for y in range(-distance, distance + 1):
            res_y: int = cords[1] + y
            if res_y >= image.height or res_y < 0:
                continue

            for x in range(-distance, distance + 1):
                res_x: int = cords[0] + x
                if res_x >= image.width or res_x < 0:
                    continue

                res: int = image.getpixel((res_x, res_y))
                if isinstance(res, int) and res >= self._line_detect:
                    return True

        return False

    def compare(self, source: IMG, comparison: IMG) -> bool:
        """
        Automates the edge detection of our source image against our comparison image to see if the images are "similar"

        Args:
            source (IMG): PIL Image
            comparison (IMG): PIL Image

        Returns:
            bool: True if the resulting image has enough matches over our `_match_threshold`
        """
        results_array: list[bool] = []
        stime: float = time.time()
        match: bool = False

        # We need to convert both images to GrayScale and run PIL Find Edges filter.
        source = self._convert(image=source)
        source = self._filter(image=source)
        comparison = self._convert(image=comparison)
        comparison = self._filter(image=comparison)

        # We need to make our source and comparison image match resolutions.
        # We also scale them down to help processing speed.
        source, comparison = self._image_resize(source=source, comparison=comparison)

        # We find all our edges, append any matches above our pixel threshold; otherwise we attempt to do a near match search.
        # After we have looked at both options; we append our bool result into our array and decide if the matches are above the threshold.
        edges: list[tuple[int, int]] | None = self._edge_detect(image=source)
        if edges is None:
            return False

        step: int = int(len(edges) / ((len(edges)) * (self._sample_percent / 100)))
        for pixel in range(0, len(edges), step):
            res: bool = self._pixel_comparison(image=comparison, cords=edges[pixel])
            if res == False:
                res: bool = self._pixel_nearmatch(image=comparison, cords=edges[pixel])
            results_array.append(res)

        counter = 0
        for entry in results_array:
            if entry == True:
                counter += 1
        self._p_match = int((counter / len(results_array)) * 100)
        if self._p_match >= self._match_percent:
            match = True
        else:
            match = False

        self._etime: float = (time.time() - stime)
        return match
