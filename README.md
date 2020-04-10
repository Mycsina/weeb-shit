# weeb-shit

A simple python script that accepts [HorribleSubs](https://horriblesubs.info) links and scrapes through it to make every episode of an anime into a magnet link.

Made with [Deluge](https://www.deluge-torrent.org/) and it's AutoAdd plugin in mind, but should work with other BitTorrent clients. Simply add the links to the list.json file and it should work fine.

### Quick tutorial
* Add HS links to list.json (configurable)

---

* Change the script to change filenames and default quality/save location
#### or
* Run it from the command line (--help for help)


## TODO

* ~~Argument parsing as ~~any~~ path changes require manual editing~~
* ~~Grouping of episodes per series on folder~~
* Auto check up on new episodes (more elegant solution to having Deluge reject all duplicates)
* Fuzzy search on HS

### Goal
* ~~Make necessary changes to have the script running as a service (proper logging perhaps)~~
* Enable the script to work with other websites