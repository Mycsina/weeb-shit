import json
import logging
import os
import re
import time
from datetime import datetime
from math import ceil


from bs4 import BeautifulSoup, SoupStrainer

import click

import requests as r

time_format = f"%d-%m-%Y %H:%M:%S"
IND = 0

# Enable if you want to try to automatize this and wish to save logs
logging.basicConfig(
    # filename=f"/logs/main-{datetime.now().strftime(time_format)}",
    # format=f"%(asctime) %(message)",
    # datefmt=f"%d/%m/%Y %I:%M%S",
    level=logging.INFO,
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
        API_page = r.get(self.requestlink).content
        soupy = BeautifulSoup(API_page, features="lxml").prettify()
        last_episode = re.search(r'id="(\d*)-1080p"', soupy)
        logging.debug(f"Most recent episode: {last_episode}")
        return int(last_episode[1])


def get_episodes(url, quality="3", save_location=os.getcwd):
    """
    Call the function and give it the HorribleSubs url and the desired quality, both as string.

    Quality is from 1 to 3 with 1 being 480p, 2 being 720p and 3 being 1080p.
    """
    global IND
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
        logging.debug(magnet)
        # Saving location
        with open(f"{save_location}/{IND}.magnet", "w+") as f:
            f.write(magnet)


def series_logger(show_id, url):
    """Given the show_id and it's url, it makes a basic log ({date} - {anime} - {ep})."""
    series_name = re.search("/shows/(.*)/", url)
    logging.info(f'{re.sub("-", " ", series_name[1]).title()} is done')
    cleaned_name = re.sub("-", " ", series_name[1]).title()
    show_ep = HSubsAPI(show_id, 0).how_many_eps()
    with open("series-log.txt", "a+") as f:
        entry = f"{datetime.now().strftime(time_format)} - {cleaned_name} - {show_ep}\n"
        f.write(entry)


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
    "--save_location",
    default=os.getcwd(),
    type=str,
    show_default=True,
    help="Where to save the .magnet files to",
)
def tasker(quality=3, individual_quality=0, save_location=os.getcwd):
    """Tasker program that loads HS links from a JSON file. And now a part-time argument handler."""
    with open("list.json", "r") as f:
        lista = json.load(f)
        individual_quality = list(individual_quality)
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
    time.sleep(5)
    dir_name = save_location
    dir_list = os.listdir(dir_name)
    for item in dir_list:
        # This was made this way because Deluge was tagging the .magnet files as .magnet.invalid even when told to delete them
        if item.endswith(".invalid"):
            os.remove(os.path.join(dir_name, item))


tasker()
