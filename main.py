import json
import logging
import re
from math import ceil
import datetime

from bs4 import BeautifulSoup, SoupStrainer

import requests as r

time_format = f"%d-%m-%Y %H:%M:%S"

logging.basicConfig(filename=f"/logs/main-{datetime.now().strftime(time_format)}", filemode="w", format=f"%(asctime) %(message)", datefmt=f"%d/%m/%Y %I:%M%S", level=logging.DEBUG)


class HSubsAPI:
    def __init__(self, show_id, page):
        """
        Build a HSubsAPI object with the requestlink attribute which points to the HorribleSubs API.

        It has the how_many_pages() method which gives back the amount of API pages there are.
        Show_id is their internal ID, page is the page number you want to access.
        """
        self.requestlink = f"https://horriblesubs.info/api.php?method=getshows&type=show&showid={show_id}&nextid={page}"
        logging.debug(f"Request link: {self.requestlink}")

    def how_many_pages(self):
        """Call it and it retrieves the amount of pages the api has on said show."""
        API_page = r.get(self.requestlink).content
        soupy = BeautifulSoup(API_page, features="lxml").prettify()
        last_episode = re.search('id="(\d*)-1080p"', soupy)
        logging.debug(f"{last_episode}")
        pages = int(last_episode[1]) / 12
        logging.debug(f"Number of pages: {pages}")
        return ceil(pages)


def get_episodes(url, quality="3"):
    """
    Call the function and give it the HorribleSubs url and the desired quality, both as string.

    Quality is from 1 to 3 with 1 being 480p, 2 being 720p and 3 being 1080p.
    """
    quality_dict = {"1": "480p", "2": "720p", "3": "1080p"}
    logging.debug(f"{quality_dict[quality_dict]}")
    page = r.get(url).content
    tags = SoupStrainer("script")
    soup = BeautifulSoup(page, features="lxml", parse_only=tags).prettify()
    show_id_group = re.search("var hs_showid = (\d*)", soup)
    show_id = show_id_group[1]
    logging.debug(show_id)
    pages = HSubsAPI(show_id, 0).how_many_pages()
    logging.debug(pages)
    entries = []
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
    i = 0
    for magnet in entries:
        i += 1
        logging.debug(magnet)
        with open(f"/home/mycsina/Desktop/{i}.magnet", "w+") as f:
            f.write(magnet)


def tasker():
    with open("list.json", "r") as f:
        lista = json.load(f)
    for entry in lista:
        logging.debug(entry)
        get_episodes(entry)


tasker()
