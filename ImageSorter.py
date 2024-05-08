# Image Sorter
# By k8thekat - 4/10/2021

import hashlib
import json
import logging
import os
import shutil
import sys
from argparse import ArgumentParser, Namespace
from configparser import ConfigParser
from io import TextIOWrapper
from pathlib import Path
from typing import Generator, TypedDict, Union

from PIL import Image


class ImageRes(TypedDict):
    """`name: str` \n
    `dimensions: tuple[int, int]`"""
    name: str
    dimensions: tuple[int, int]


class ImageSorter:
    def __init__(self) -> None:
        parser = ArgumentParser(description="Python Image Sorter")
        parser.add_argument("-f", help="The path to your settings.ini", required=False, type=Path)
        self._args: Namespace = parser.parse_args()

        logging.basicConfig(format="%(asctime)s [%(levelname)s]  %(message)s", level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p', handlers=[logging.StreamHandler(sys.stdout)])
        self._logger = logging.getLogger()

        self._ImageResolutions: list[ImageRes] = [
            {"name": "Low Res", "dimensions": (1440, 900)},
            {"name": "Mid Res", "dimensions": (1920, 1440)},
            {"name": "High Res", "dimensions": (2560, 1600)},
            {"name": "UHD Res", "dimensions": (3840, 2160)},
            {"name": "UHDP Res", "dimensions": (9000, 9000)},
            {"name": "Phone Res", "dimensions": (1080, 2400)}]

        # default directories
        self._source_dir: Path
        self._destination_dir: Path
        self._directories: dict[str, str] = {
            "_source_dir": "Source directory:",
            "_destination_dir": "Destination directory:"}

        # util
        self._hash_file: Path = Path.cwd().joinpath("hashdatabase.json")
        self._temp_hash_list: dict[str, str] = {}  # {"b7abe0e999528837a9588bdf82f37183262b9f0775772491468a78107c285d96": "h:\\picture\\anime\\037533e1272fd9f6fd860abac4c5f1c3.png"}
        self._duplicate_images: list[Path] = []

        # sort settings
        self._sort_wallpapers: bool = False
        self._sort_recursive: bool = False
        self._hash_pictures: bool = False
        self._settings: dict[str, str] = {
            "_sort_wallpapers": "Would you like to separate Wallpaper sized pictures into their own folder? 'y/N' (default: N): ",
            "_sort_recursive": "Would you like the search to recursive? 'y/N' (default: N): ",
            "_hash_pictures": "Would you like to check for duplicate images? 'y/N' (default: N): "}

        # these settings can be changed via `settings.ini`
        self._file_types: tuple[str, ...] = (".png", ".jpg", ".webp", ".jpeg")
        self._ignore_directories: list[str] | str = ["Low Res", "Mid Res", "High Res", "UHD Res", "Phone Res", "UHDP Res", "Wallpapers"]
        self._scale_factor: float = 1.3

        self._use_default: bool = True  # default to prompts always..

    def start(self) -> None:
        """Call to loading settings and start sorting.
        """
        if self._args.f:
            self._load_settings()

        # prompt setting change (if no file)
        if self._use_default:
            self._user_settings_prompts()
            self._user_directory_prompts()

        self._image_dir_creation()
        if self._hash_pictures:
            self._hash_database_load()

        self._image_sort(self._image_list_generator())

        # done sorting; so lets prompt our duplicate deletion.
        if len(self._duplicate_images) > 5:
            self._delete(bulk=True)
        else:
            self._delete()

        self._hash_database_save()
        self._logger.info("Finished sorting...")

    def _load_settings(self) -> None:
        """If the user passed in a `settings.ini` to the `-f` arg; this will load the settings. 

        If successful; sets `self._use_default = False`"""
        self._setting_file: Path = Path(self._args.f)

        # this check does two things; verify the path exists and the file exists.
        if self._setting_file.is_file():
            # open config file
            settings = ConfigParser(converters={"list": lambda setting: [value.strip() for value in setting.split(",")]})
            # read config file
            settings.read(self._setting_file.as_posix())
            # directories
            self._source_dir = Path(settings.get("DIRECTORIES", "SOURCE"))
            self._destination_dir = Path(settings.get("DIRECTORIES", "DESTINATION"))
            # need to validate SOURCE and DESTINATION
            if not self._source_dir.exists():
                self._logger.error(f"The SOURCE path you provided is not valid. -> {self._source_dir}")
                sys.exit(1)
            if not self._destination_dir.exists():
                self._logger.error(f"The DESTINATION path you provided is not valid. -> {self._destination_dir}")
                sys.exit(1)

            # wallpapers
            self._sort_wallpapers = settings.getboolean("WALLPAPERS", "SORT")
            self._scale_factor = settings.getfloat("WALLPAPERS", "SCALE_FACTOR")

            # settings
            self._sort_recursive = settings.getboolean("SETTINGS", "RECURSIVE")
            self._hash_pictures = settings.getboolean("SETTINGS", "HASH")
            self._file_types = tuple(settings.get("SETTINGS", "FILE_TYPES"))
            self._ignore_directories = settings.get("SETTINGS", "IGNORE_DIR")

            self._use_default = False
            self._logger.info("Finished loading settings.ini")

        else:  # If the file doesn't exist or is improper; use default settings.
            self._logger.error("Failed to load Settings; reverting to default Settings.")

    def _user_directory_prompts(self) -> None:
        """Prompt for user input of Source/Destination directories"""
        for key, value in self._directories.items():
            while 1:
                user_choice: str = input(value)
                # if no entry; exit..
                if len(user_choice) == 0:
                    self._logger.critical("Exiting...")
                    sys.exit(1)

                # validate the path
                if Path(user_choice.strip()).exists():
                    self.__setattr__(key, Path(user_choice.strip()))
                    break
                else:
                    self._logger.error("Directory does not exist; please re-enter.")

    def _user_settings_prompts(self) -> None:
        """Prompts configuration choices to determine how to sort.

        `self._sort_wallpapers: bool = False`
        `self._sort_recursive: bool = False`
        `self._hash_pictures: bool = False`
        """
        for key, value in self._settings.items():
            while 1:
                user_choice: str = input(value)
                # if no entry; use default and break to next entry.
                if len(user_choice) == 0:
                    break

                elif user_choice.lower() == "y":
                    self.__setattr__(key, True)
                    break

                # if the results DON'T match y or n; prompt again.
                elif not user_choice.lower() == "n":
                    self._logger.error("Your entry was invalid; please select between (y/N)")

    def _image_dir_creation(self) -> None:
        """ Creates Directories based upon `self._ImageResolutions` "name" field."""
        for entry in self._ImageResolutions:
            cur_path: Path = self._destination_dir.joinpath(entry["name"])
            if not cur_path.exists():
                cur_path.mkdir()
                self._logger.info(entry["name"] + " folder created!")

        if self._sort_wallpapers:
            cur_path: Path = self._destination_dir.joinpath("Wallpapers")
            if not cur_path.exists():
                cur_path.mkdir()
                self._logger.info("Wallpapers folder created!")

    def _image_list_generator(self) -> list[Path]:
        """Creates a list of Path objects of all images that match `self._file_types`.

        IF `self._sort_recursive == True` it will also `glob` all matching `file_types` of sub directories."""
        _image_list: list = []
        for file in self._source_dir.iterdir():
            if file.is_file() and file.name.lower().endswith(self._file_types):
                _image_list.append(file)

            if file.is_dir():
                # Ignore our self._destination_path if it is in the same directory as self._source_path.
                if str(file.absolute()) == self._destination_dir or file.name in self._ignore_directories:
                    # self._logger.warn(f"Found an unwanted directory {file.name}; skipping~")
                    continue

                if self._sort_recursive:
                    for suffix in self._file_types:
                        file_list: Generator[Path, None, None] = file.glob(("*" + suffix))
                        for sub_file in file_list:
                            _image_list.append(sub_file)

        return _image_list

    def _image_sort(self, image_list: list[Path]) -> None:
        """Sorts images into their respective resolution boundaries specified by `self._ImageResolutions` or into a `Wallpaper` folder if enabled."""
        move: int = 0
        cur_image: Union[Image.Image, None] = None
        imagewidth: int
        imageheight: int
        self._logger.info(f"Found {len(image_list)} images to sort...")
        for image in image_list:
            _output_dir: Path = self._destination_dir
            _wallpaper: bool = False
            cur_image_hash: str = hashlib.sha256(open(image.as_posix(), "rb").read()).hexdigest()
            try:
                cur_image = Image.open(image)

            except Exception as e:
                self._logger.error(f"We encountered an error opening {image.name} | Exception: {e}")
                continue

            # image sorting of wallpapers
            if self._sort_wallpapers:
                if (cur_image.width / cur_image.height) > self._scale_factor:
                    # Close the image so we dont get a file access error.
                    cur_image.close()
                    _output_dir = self._destination_dir.joinpath("Wallpapers")
                    _wallpaper = True

            # image sorting via dictionary dimensions comparison" > = GREATER THAN | < = LESS THAN "
            if not _wallpaper:
                # imageres is the dictionary with all dimensions
                # range function starts at X value and ends at Y-1 (range(X,Y-1)) count = interation value
                # value 1, value 2 = IMGRES[int][dictionary key]
                # if value 1 >= cur_image.width(opened image) and value 2 >= cur_image.height(opened image)
                for move in range(0, len(self._ImageResolutions)):
                    imagewidth, imageheight = self._ImageResolutions[move]["dimensions"]
                    if not (imagewidth >= cur_image.width) and not (imageheight >= cur_image.height):
                        cur_image.close()
                        continue

                    else:
                        cur_image.close()
                        _output_dir = self._destination_dir.joinpath(self._ImageResolutions[move]["name"])

            if self._hash_pictures:
                if cur_image_hash not in self._temp_hash_list:
                    self._temp_hash_list[cur_image_hash] = _output_dir.joinpath(image.name).as_posix()
                else:
                    if self._validate_file_hash(image, cur_image_hash, _output_dir.joinpath(image.name)):
                        continue

            # Move our image to the destination path we set.
            try:
                shutil.move(image.as_posix(), _output_dir)
                self._logger.info(f'Moved {image.name} | {self._source_dir.as_posix()} >> {_output_dir.as_posix()}')

            except shutil.Error as e:
                # we only care about duplicate file/path issues.
                if isinstance(e.args[0], str) and e.args[0].startswith("Destination path"):  # type:ignore
                    # This typically triggers if the image failed the _validate_file_hash.
                    if image in self._duplicate_images:
                        continue

                    # Try to move picture A into dir; dir has pic A already (so we will call it pic B). We compare the has of pic A to pic B.
                    # if the has of pic A and pic B match; we should skip moving pic A entirely.
                    _image_output: str = _output_dir.joinpath(image.name).as_posix()
                    # file hash comparison => open(file), "rb" = read binary , read file and digest = hash results
                    file2hash: str = hashlib.sha256(open(_image_output, "rb").read()).hexdigest()
                    if cur_image_hash == file2hash:
                        self._duplicate_images.append(image)
                        continue

                    else:
                        _num_increment: int = 1
                        _file_output: str = _output_dir.as_posix() + "/" + image.stem + "_" + str(_num_increment) + image.suffix
                        while (Path(_file_output).exists()):
                            _num_increment += 1
                        try:
                            new_image: Path = image.rename(_file_output)
                            self._logger.warning(msg="Duplicate file name found at " + _image_output + " --> Renaming file..." + new_image.name)
                        except OSError as e:
                            self._logger.error(msg=f"We encountered an error renaming {image.name} | Exception: {e}")
                            continue
                        # shutil.move(self._source_dir.as_posix() + file.name, fileoutname[0:dotloc] + str(filenum) + fileoutname[dotloc:])
                else:
                    self._logger.error(f"We encountered an error moving {image.name} | Exception: {e}")

            except PermissionError as e:
                self._logger.error(f"We encountered a Permissions Error when moving {image.name} | Exception: {e}")

            except OSError as e:
                self._logger.error(msg="We encountered an error moving " + image.name + f" | Exception: {e}")
                continue

    def _hash_database_load(self) -> None:
        """Loads our `hashdatabase.json` if it exists; otherwise creates the file in the current working directory."""
        temp_file: TextIOWrapper
        if self._hash_file.exists():
            temp_file = open(self._hash_file)

            try:
                self._temp_hash_list = json.load(temp_file)
            except json.decoder.JSONDecodeError as e:
                self._logger.error(f"We encountered a Decode Error when loading hashdatabase.json | Exception: {e}")
                temp_file.close()
                return

            temp_file.close()
            self._logger.info("loaded hashdatabase.json")

        else:
            temp_file = open(self._hash_file, "x")
            temp_file.close()
            self._logger.warning("Unable to find hashdatabase.json, creating the database.")

    def _hash_database_save(self) -> None:
        """Hash List Save"""
        temp_file: TextIOWrapper = open(self._hash_file, "w")  # w = overwrite
        # saves my hash list to a new file with each entry spaced out by a new line.
        try:
            json.dump(self._temp_hash_list, temp_file, indent="\n")
        except Exception as e:
            self._logger.error(f"We encountered an Error when saving our hashdatabase.json | Exception: {e}")
            temp_file.close()
            return

        temp_file.close()
        self._logger.info("Saved hashdatabase.json")
        return

    def _delete(self, bulk: bool = False) -> None:
        """ Prompts users with a choice to delete images from `self._duplicate_images`"""
        _confirm: str = "n"
        _exit: bool = False
        _count: int = len(self._duplicate_images)
        self._logger.info(f"Found {_count} duplicate images...")

        for image in self._duplicate_images:
            reply: str = "Delete duplicate file? " + self._source_dir.joinpath(image.name).as_posix() + "(y/N)? :"
            if _confirm == "y":
                os.remove(image.as_posix())
                continue

            elif _exit:
                break

            while 1:
                if bulk:
                    reply = f"Delete all {(_count)} duplicate images (y/N)? :"

                confirm: str = input(reply).lower()
                if len(confirm) == 0 or confirm == "n":
                    if bulk:
                        _exit = True
                    break

                elif confirm == "y":
                    if bulk:
                        _confirm = "y"
                    os.remove(image.as_posix())
                    break

                elif confirm != "n":
                    self._logger.error("Your entry was invalid; please select between 'y/N'")
                    continue

    def _validate_file_hash(self, image_dir: Path, image_hash: str, image_output_path: Path) -> bool | None:
        """Compares the hash of the current image against the hash of the image in the DB.
         If the current image hash exists in the DB.
            We use the existing hash and open the file path it specifies.

            `IF the file path NO LONGER exists` we update the DB with the current image's output directory and hash then continue.

            `ELSE` We then re-hash the file path from the DB against the current image hash;

         `IF they MATCH` we add the current image as a duplicate image and prompt deletion later.

         `IF they DO NOT` match we update the file path with the current image's output directory (if it changes) and continue.

         `IF` by any chance the hash of the existing file path already exists; we continue the above process of the existing image against the DB's existing image path.. etc etc..
         """
        # need to compare the new image and the old image hashs
        # need to update the hash list if they no longer match.
        # using the "hash" that already exists as a key to get a Path(str)
        _existing_file: Path = Path(self._temp_hash_list[image_hash])

        # if the hash path is invalid; update the hash and the path entry.
        if not _existing_file.exists():
            self._temp_hash_list[image_hash] = image_output_path.as_posix()
            return False

        # the file path exists; compare the old image to the new one.
        else:
            _temp_hash: str = hashlib.sha256(open(_existing_file.as_posix(), "rb").read()).hexdigest()
            if _temp_hash == image_hash:
                self._duplicate_images.append(image_dir)
                return True

            elif _temp_hash not in self._temp_hash_list:
                # first we update our DB with the new hash and get its path using the old hash.
                # then we update the old hash with a new path.
                self._temp_hash_list[_temp_hash] = _existing_file.as_posix()
                self._temp_hash_list[image_hash] = image_output_path.as_posix()

            else:
                # if the new hash is "somehow" in the DB already; perform a validation.
                self._validate_file_hash(_existing_file, _temp_hash, image_output_path)


if __name__ == "__main__":
    ImageSorter().start()
