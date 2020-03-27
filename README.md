# weeb-shit

A simple python script that accepts [HorribleSubs](https://horriblesubs.info) links and scrapes through it to make every episode of an anime into a magnet link.

Made for [Deluge](https://www.deluge-torrent.org/) and it's AutoAdd plugin. Simply add the links to the list.json file and it should work fine.

### Quick tutorial
* Add series to a file named list.json (configurable)
* Change the folder where to save and then run it with the default settings (1080p) 
```bash
python /weeb_shit/main.py
```
#### or 

Run it from the command line (--help for help)


## TODO

* Argument parsing as ~~any~~ path changes require manual editing
* Grouping of episodes per series on folder
* Auto check up on new episodes (more elegant solution to having Deluge reject all duplicates)

### Goal
* Make necessary changes to have the script running as a service (proper logging perhaps)