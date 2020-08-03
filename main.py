import json
import logging
import os
import re
import time
from datetime import datetime
from math import ceil
from shutil import move

from bs4 import BeautifulSoup, SoupStrainer

import click

import requests as r

time_format = f"%d-%m-%Y %H:%M:%S"
count = 0
CWD = os.getcwd()
__LOCATION__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


# Enable if you want to try to automatize this and wish to save logs
def mod_logging(logging_level):
    """Just modified logging."""
    logging.basicConfig(
        # filename=f"/logs/main-{datetime.now().strftime(time_format)}",
        # format=f"%(asctime) %(message)",
        # datefmt=time_format,
        level=logging_level
    )


class HSubsAPI:
    """
    Class for HorribleSubs.info anime shows' API links.

    | Attributes |

    requestlink_prototype (str/URL) = Links towards the shows' API page. Indicate which page you wish to access by adding the number to the string.

    | Methods |

    how_many_pages\n
    how_many_eps
    """

    def __init__(self, show_id):
        """
        Constructor function for the HSubsAPI class.

        | Parameters |

        show_id (str) = HSubs internal show ID. Look for "var hs_showid =" on the show's page source code
        """
        self.requestlink_prototype = (
            f"https://horriblesubs.info/api.php?method=getshows&type=show&showid={show_id}&nextid="
        )
        logging.debug(f"Request link: {self.requestlink_prototype}")

    def episode_listing(self):
        """Returns the episodes released."""
        page = -1
        episodes = []
        while True:
            page += 1
            actual_request_link = f"{self.requestlink_prototype}{page}"
            if (
                re.search(r"DONE", BeautifulSoup(r.get(actual_request_link).content, features="lxml").prettify())
                is None
            ):
                for episode in re.findall(
                    r'id="(\d*-?\d*)-1080p"',
                    BeautifulSoup(r.get(actual_request_link).content, features="lxml").prettify(),
                ):
                    episodes.append(episode)
            else:
                break
        return episodes


def get_episodes(url, quality="3", save_location=CWD):
    """
    Call the function and give it the HorribleSubs url and the desired quality, both as string.

    Quality is from 1 to 3 with 1 being 480p, 2 being 720p and 3 being 1080p.

    |Args|
        - url: HorribleSubs url
        - quality: 1 - 480, 2 - 720, 3 - 1080
        - save_location: String (Default = Current working directory)
    """
    global count
    global CWD
    quality_dict = {"1": "480p", "2": "720p", "3": "1080p"}
    logging.debug(f"{quality_dict[quality]}")
    soup = BeautifulSoup(r.get(url).content, features="lxml", parse_only=SoupStrainer("script")).prettify()
    show_id = re.search(r"var hs_showid = (\d*)", soup)[1]
    logging.debug(show_id)
    ep_number = len(HSubsAPI(show_id).episode_listing())
    logging.debug(ep_number)
    entries = []
    series_logger(show_id, url)
    page_count = ceil(ep_number / 12)
    while page_count != 0:
        page_count -= 1
        page = BeautifulSoup(
            r.get(f"{HSubsAPI(show_id).requestlink_prototype}{page_count}").content,
            features="lxml",
            parse_only=SoupStrainer("div"),
        )
        for link in page.find_all(class_=f"rls-link link-{quality_dict[quality]}"):
            logging.debug(str(link) + "\n")
            entries.append(re.search('href="(.*)" title="Magnet', str(link))[1])
    for magnet in entries:
        count += 1
        # Saving location
        with open(f"{save_location}/{count}.magnet", "w+") as f:
            f.write(magnet)


def series_logger(show_id, url):
    """Given the show_id and it's url, it makes a basic log ({date} - {anime} - {ep}).

    |Args|
        - show_id: HSubs API show_id
        - url: HSubs page url
    """
    global CLEANED_NAME
    series_name = re.search(r"/shows/(.*)/", url)
    cleaned_name = re.sub(r"-", r" ", series_name[1]).title()
    episode_listing = HSubsAPI(show_id).episode_listing()
    logging.info(f"Most recent episode: {episode_listing[0]} | Total number of episodes {len(episode_listing)}")
    logging.info(f"{cleaned_name} is done")
    entry = f"{datetime.now().strftime(time_format)} - {cleaned_name} - {episode_listing[0]} - Downloaded {len(episode_listing)} episodes\n"
    with open(os.path.join(__LOCATION__, "series-log.txt"), "a+") as f:
        f.write(entry)


def organizer(src_path, save_location):
    """Sorts downloaded HorribleSubs episodes per anime in folders. First argument is where to search in, second is the desired save location.

    |Args|
        - src_path: Path with disorganized files
        - save_location: Organized files destination folder
    """
    dir_list = os.listdir(src_path)
    for entry in dir_list:
        if re.search(r"\[HorribleSubs\] (.*) -", entry):
            series_name = re.search(r"\[HorribleSubs\] (.*) -", entry)[1]
            logging.debug(series_name)
            try:
                os.mkdir(f"{save_location}/{series_name}")
            except OSError:
                pass
            move(f"{src_path}/{entry}", f"{save_location}/{series_name}/{entry}")
            logging.debug(f"Moved {src_path}/{entry} to {save_location}/{series_name}/{entry}")
        else:
            logging.debug(f"This entry {entry} ain't it, chief.")


def tasker(quality, individual_quality, save_location):
    """Loads links from set file."""
    try:
        with open(os.path.join(__LOCATION__, "list.json"), "r") as f:
            lista = json.load(f)
    except FileNotFoundError:
        with open(os.path.join(__LOCATION__, "list.json"), "w+") as f:
            json.dump([], f)
        raise UnboundLocalError("Run again")
    for entry in lista:
        if int(individual_quality[1]) == 1:
            individual_quality[1] = int(individual_quality[1]) - 1
            logging.info(f"Working on: {entry}")
            logging.info(f"Working with custom quality type {individual_quality[0]}")
            get_episodes(entry, individual_quality[0], save_location)
        else:
            individual_quality[1] = int(individual_quality[1]) - 1
            logging.info(f"Working on: {entry}")
            get_episodes(entry, quality, save_location)
        # Make sure that the torrent client has time to add all of the .magnet files
    time.sleep(count / 5)
    for item in os.listdir(save_location):
        # This was made this way because Deluge was tagging the .magnet files as .magnet.invalid even when told to delete them
        if item.endswith(".invalid"):
            logging.debug(f"Removed {os.path.join(save_location, item)}")
            os.remove(os.path.join(save_location, item))


def hsubs_bk():
    """Puts all HSubs shows into the queue file to be downloaded."""
    page = r.get("https://horriblesubs.info/shows/")
    steamed = BeautifulSoup(page.content, features="lxml", parse_only=SoupStrainer("a"))
    steamed.find(title="All shows").decompose()
    anime_list = []
    for entry in steamed.find_all(href=re.compile(r"/shows/")):
        anime_list.append(re.search(r"<a href=\"(.*)\" ", str(entry))[1])
    anime_list = [f"https://horriblesubs.info{entry}" for entry in anime_list]
    with open("list.json", "w+") as f:
        json.dump(anime_list, f)


@click.command()
@click.option(
    "-Q",
    "--quality",
    default="3",
    type=str,
    show_default=True,
    help="1 is 480p, 2 is 720p and 3 is 1080p. Applies to all entries",
)
@click.option(
    "-q",
    "--individual-quality",
    nargs=2,
    default=("3", "0"),
    type=str,
    show_default=True,
    help="First entry is for the quality (1: 480p, 2: 720p, 3: 1080p). Second is for which entry should be different (1 -> 1st entry, 3 -> 3rd entry)",
)
@click.option(
    "-s",
    "--save-location",
    default=CWD,
    type=str,
    show_default=True,
    help="Where to save the .magnet files to; if used with -o flag, sets the folder in which series folders will be created.",
)
@click.option(
    "-O",
    "--organize",
    is_flag=True,
    default=False,
    show_default=True,
    help="If the script should try to sort any loose HorribleSubs episodes per anime into countividual folders. Run it from the folder you want to get sorted and use the -s flag to customize where should the files go. Running it with this option won't download the .magnet files",
)
@click.option(
    "-c", "--clean", is_flag=True, default=False, show_default=True, help="Cleans all created files",
)
@click.option(
    "-b", "--backup", is_flag=True, default=False, show_default=True, help="Puts all HSubs shows into the queue file"
)
@click.option(
    "-l",
    "--logging-level",
    default=2,
    show_default=True,
    help="Default logging level is info (2), can be set to debug (1) to make the logging more verbose. 3 will not log any information, with exception of critical errors",
)
def argparser(
    quality="3", individual_quality=None, save_location=CWD, organize=False, clean=False, logging_level=2, backup=False
):
    """Simple argument parser for the click module."""
    logging_dict = {1: logging.DEBUG, 2: logging.INFO, 3: logging.CRITICAL}
    individual_quality = list(individual_quality)
    mod_logging(logging_dict[logging_level])
    if backup:
        hsubs_bk()
    if organize:
        organizer(CWD, save_location)
    else:
        tasker(quality, individual_quality, save_location)
        if clean:
            with open(os.path.join(__LOCATION__, "list.json"), "w+") as f:
                json.dump([], f)
                logging.info("Job finished!")
            for item in os.listdir(save_location):
                if item.endswith(".magnet"):
                    logging.debug(f"Removed {os.path.join(save_location, item)}")
                    os.remove(os.path.join(save_location, item))
            try:
                os.remove("series-log.txt")
            except FileNotFoundError:
                pass
        else:
            logging.info("Job finished!")


# hsubs_bk()
if __name__ == "__main__":
    argparser()
