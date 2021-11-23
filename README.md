# MijnOVScraper

Previously this data was easily accesible through the API used by the mobile app. But since the app got taken down, so did the API endpoint. I still wanted to fetch my traveling data, so I've thrown together this scraper that scrapes the data from the ov-chipkaart.nl site.

It generated a data.json file similar to the old format the api would return. 

You only need to create a settings.py file, with the following:
```
MEDIUM_ID = "<id of the card you want to fetch for>"
LOGIN_USERNAME = "<your username on ov-chipkaart.nl>"
LOGIN_PASSWORD = "<your password on ov-chipkaart.nl>"
```

MEDIUM_ID can be get by going to [this](https://www.ov-chipkaart.nl/mijn-ov-chip/mijn-ov-reishistorie.htm) page, and selecting your card. In the url it will display your 'mediumid'.
You can also login manually in the browser opened by the selenium web driver, instead of setting it through the settings file.
