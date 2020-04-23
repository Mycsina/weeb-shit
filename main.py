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
IND = 0
CLEANED_NAME = ""
CWD = os.getcwd()
__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))
logging_dict = {1: logging.DEBUG, 2: logging.INFO, 3: logging.CRITICAL}


# Enable if you want to try to automatize this and wish to save logs
def mod_logging(level_dict):
    """Just modified logging."""
    logging.basicConfig(
        # filename=f"/logs/main-{datetime.now().strftime(time_format)}",
        # format=f"%(asctime) %(message)",
        # datefmt=time_format,
        level=level_dict
    )


class HSubsAPI:
    def __init__(self, show_id, page):
        """
        Build a HSubsAPI object with the requestlink attribute which points to the HorribleSubs API.

        It has the how_many_pages() method which gives back the amount of API pages there are. The how_many_eps() is clear enough.
        Show_id is their internal ID, page is the page number you want to access.
        """
        self.requestlink = f"https://horriblesubs.info/api.php?method=getshows&type=show&showid={show_id}&nextid={page}"
        logging.debug(f"Request link: {self.requestlink}")

    def how_many_pages(self):
        """Call it and it retrieves the amount of pages the api has on said show."""
        pages = self.how_many_eps() / 12
        logging.debug(f"Number of pages: {pages}")
        return ceil(pages)

    def how_many_eps(self):
        """Call it and it retrieves the number of episodes released."""
        api_page = r.get(self.requestlink).content
        soupy = BeautifulSoup(api_page, features="lxml").prettify()
        last_episode = re.search(r'id="(\d*)-1080p"', soupy)
        logging.debug(f"Most recent episode: {last_episode[1]}")
        return int(last_episode[1])


def get_episodes(url, quality="3", save_location=CWD):
    """
    Call the function and give it the HorribleSubs url and the desired quality, both as string.

    Quality is from 1 to 3 with 1 being 480p, 2 being 720p and 3 being 1080p.
    """
    global IND
    global CLEANED_NAME
    global CWD
    quality_dict = {"1": "480p", "2": "720p", "3": "1080p"}
    logging.debug(f"{quality_dict[quality]}")
    page = r.get(url).content
    tags = SoupStrainer("script")
    soup = BeautifulSoup(page, features="lxml", parse_only=tags).prettify()
    show_id_group = re.search(r"var hs_showid = (\d*)", soup)
    show_id = show_id_group[1]
    logging.debug(show_id)
    pages = HSubsAPI(show_id, 0).how_many_pages()
    logging.debug(pages)
    entries = []
    series_logger(show_id, url)
    while pages != 0:
        pages -= 1
        series_api = BeautifulSoup(
            r.get(HSubsAPI(show_id, pages).requestlink).content, features="lxml"
        )
        for link in series_api.find_all(
            "div", f"rls-link link-{quality_dict[quality]}"
        ):
            logging.debug(str(link) + "\n")
            entries.append(re.search('href="(.*)" title="Magnet', str(link))[1])
    for magnet in entries:
        IND += 1
        logging.debug(f"Magnet link: {magnet}")
        # Saving location
        with open(f"{save_location}/{IND}.magnet", "w+") as f:
            f.write(magnet)


def series_logger(show_id, url):
    """Given the show_id and it's url, it makes a basic log ({date} - {anime} - {ep})."""
    global CLEANED_NAME
    series_name = re.search(r"/shows/(.*)/", url)
    logging.info(f'{re.sub(r"-", r" ", series_name[1]).title()} is done')
    CLEANED_NAME = re.sub(r"-", r" ", series_name[1]).title()
    show_ep = HSubsAPI(show_id, 0).how_many_eps()
    entry = f"{datetime.now().strftime(time_format)} - {CLEANED_NAME} - {show_ep}\n"
    with open(os.path.join(__location__, "series-log.txt"), "a+") as f:
        f.write(entry)


def organizer(src_path, save_location):
    """Sorts downloaded HorribleSubs episodes per anime in folders. First argument is where to search in, second is the desired save location."""
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
            logging.debug(f"This entry:{entry} ain't it, chief.")


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
    help="First entry is for the quality (1: 480p, 2: 720p, 3: 1080p). Second is for which entry should be different (1 -> 1st entry, 3 -> 3rd entry",
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
    "-o",
    "--organize",
    is_flag=True,
    default=False,
    show_default=True,
    help="If the script should try to sort any loose HorribleSubs episodes per anime into individual folders. Run it from the folder you want to get sorted and use the -s flag to customize where should the files go. Running it with this option won't download the .magnet files",
)
@click.option(
    "-c",
    "--clean",
    is_flag=True,
    default=False,
    show_default=True,
    help="Cleans the list.json file after creating all .magnet files",
)
@click.option(
    "-l",
    "--logging-level",
    default=2,
    show_default=True,
    help="Default logging level is info (2), can be set to debug (1) to make the logging more verbose. 3 will not log any information, with exception of critical errors"
)
def tasker(
    quality="3", individual_quality="0", save_location=CWD, organize=False, clean=False, logging_level=2
):
    """Tasker program that loads HS links from a JSON file. And now a part-time argument handler."""
    mod_logging(logging_dict[logging_level])
    if organize:
        organizer(CWD, save_location)
    else:
        with open(os.path.join(__location__, "list.json"), "r") as f:
            lista = json.load(f)
            individual_quality = list(individual_quality)
        for entry in lista:
            if int(individual_quality[1]) == 1:
                individual_quality[1] = int(individual_quality[1]) - 1
                logging.info(f"Working on: {entry}")
                logging.info(
                    f"Working with custom quality type {individual_quality[0]}"
                )
                get_episodes(entry, individual_quality[0], save_location)
            else:
                individual_quality[1] = int(individual_quality[1]) - 1
                logging.info(f"Working on: {entry}")
                get_episodes(entry, quality, save_location)
        # Make sure that the torrent client has time to add all of the .magnet files
        time.sleep(IND / 5)
        dir_name = save_location
        dir_list = os.listdir(dir_name)
        for item in dir_list:
            # This was made this way because Deluge was tagging the .magnet files as .magnet.invalid even when told to delete them
            if item.endswith(".invalid"):
                os.remove(os.path.join(dir_name, item))
        if clean:
            with open(os.path.join(__location__, "list.json"), "w+") as f:
                json.dump([], f)
                logging.info("Job finished!")
        else:
            logging.info("Job finished!")


tasker()
