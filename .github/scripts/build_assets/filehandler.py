import json
from zipfile import ZipFile
from pathlib import Path
from typing import List
import os
import re


def find_new_icons(devicon_json_path: str, icomoon_json_path: str) -> List[dict]:
    """
    Find the newly added icons by finding the difference between
    the devicon.json and the icomoon.json.
    :param devicon_json_path, the path to the devicon.json.
    :param icomoon_json_path: a path to the iconmoon.json.
    :return: a list of the new icons as JSON objects.
    """
    with open(devicon_json_path) as json_file:
        devicon_json = json.load(json_file)

    with open(icomoon_json_path) as json_file:
        icomoon_json = json.load(json_file)

    new_icons = []
    for icon in devicon_json:
        if is_not_in_icomoon_json(icon, icomoon_json):
            new_icons.append(icon)

    return new_icons


def is_not_in_icomoon_json(icon, icomoon_json) -> bool:
    """
    Checks whether the icon's name is not in the icomoon_json.
    :param icon: the icon object we are searching for.
    :param icomoon_json: the icomoon json object parsed from
    icomoon.json.
    :return: True if icon's name is not in the icomoon.json, else False.
    """
    pattern = re.compile(f"^{icon['name']}-")

    for font in icomoon_json["icons"]:
        if pattern.search(font["properties"]["name"]):
            return False
    return True


def get_svgs_paths(new_icons: List[dict], icons_folder_path: str) -> List[str]:
    """
    Get all the suitable svgs file path listed in the devicon.json.
    :param new_icons, a list containing the info on the new icons.
    :param icons_folder_path, the path where the function can find the
    listed folders.
    :return: a list of svg file paths that can be uploaded to Icomoon.
    """
    file_paths = []
    for icon_info in new_icons:
        folder_path = Path(icons_folder_path, icon_info['name'])

        if not folder_path.is_dir():
            raise ValueError(f"Invalid path. This is not a directory: {folder_path}.")

        # TODO: remove the try-except when the devicon.json is upgraded
        try:
            aliases = icon_info["aliases"]
        except KeyError:
            aliases = [] # create empty list of aliases if not provided in devicon.json

        for font_version in icon_info["versions"]["font"]:
            # if it's an alias, we don't want to make it into an icon
            if is_alias(font_version, aliases):
                print(f"Not exist {icon_info['name']}-{font_version}.svg")
                continue

            file_name = f"{icon_info['name']}-{font_version}.svg"
            path = Path(folder_path, file_name)

            if path.exists():
                file_paths.append(str(path))
            else:
                raise ValueError(f"This path doesn't exist: {path}")

    return file_paths


def is_alias(font_version: str, aliases: List[dict]):
    """
    Check whether the font version is an alias of another version.
    :return: True if it is, else False.
    """
    for alias in aliases:
        if font_version == alias["alias"]:
            return True
    return False


def extract_files(zip_path: str, extract_path: str, delete=True):
    """
    Extract the style.css and font files from the devicon.zip
    folder. Must call the gulp task "get-icomoon-files"
    before calling this.
    :param zip_path, path where the zip file returned
    from the icomoon.io is located.
    :param extract_path, the location where the function
    will put the extracted files.
    :param delete, whether the function should delete the zip file
    when it's done.
    """
    print("Extracting zipped files...")

    icomoon_zip = ZipFile(zip_path)
    target_files = ('selection.json', 'fonts/', 'fonts/devicon.ttf',
                    'fonts/devicon.woff', 'fonts/devicon.eot',
                    'fonts/devicon.svg', "style.css")
    for file in target_files:
        icomoon_zip.extract(file, extract_path)

    print("Files extracted")

    if delete:
        print("Deleting devicon zip file...")
        icomoon_zip.close()
        os.remove(zip_path)


def rename_extracted_files(extract_path: str):
    """
    Rename the extracted files selection.json and style.css.
    :param extract_path, the location where the function
    can find the extracted files.
    :return: None.
    """
    print("Renaming files")
    old_to_new_list = [
        {
            "old": Path(extract_path, "selection.json"),
            "new": Path(extract_path, "icomoon.json")
        },
        {
            "old": Path(extract_path, "style.css"),
            "new": Path(extract_path, "devicon.css")
        }
    ]

    for dict_ in old_to_new_list:
        os.replace(dict_["old"], dict_["new"])

    print("Files renamed")


def create_screenshot_folder(dir, screenshot_name: str="screenshots/"):
    """
    Create a screenshots folder in the dir.
    :param dir, the dir where we want to create the folder.
    :param screenshot_name, the name of the screenshot folder.
    :raise Exception if the dir provided is not a directory.
    :return the string name of the screenshot folder.
    """
    folder = Path(dir).resolve()
    if not folder.is_dir():
        raise Exception(f"This is not a dir: {str(folder)}. \ndir must be a valid directory")

    screenshot_folder = Path(folder, screenshot_name)
    try:
        os.mkdir(screenshot_folder)
    except FileExistsError:
        print(f"{screenshot_folder} already exist. Script will do nothing.")
    finally:
        return str(screenshot_folder)
