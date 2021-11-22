import json

import requests
import os
from datetime import datetime
import pathlib
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from settings import *
from webdriver_manager.chrome import ChromeDriverManager

# Start selenium webdriver
chrome_options = Options()
scriptDirectory = pathlib.Path().absolute()
chrome_options.add_argument(f"--user-data-dir={scriptDirectory}\\chrome-data-temp")

history_base_url = "https://www.ov-chipkaart.nl/mijn-ov-chip/mijn-ov-reishistorie.htm"
driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
driver.get(history_base_url)

default_timeout = 10


loaded_entries = []

def scrape(formatted_begin_date, formatted_end_date, pagenum):
    driver.get(f"{history_base_url}?mediumid={MEDIUM_ID}&begindate={formatted_begin_date}&enddate={formatted_end_date}&pagenumber={pagenum}")
    driver.implicitly_wait(default_timeout)
    elements = driver.find_elements_by_class_name("known-transaction")

    if len(elements) != 0:
        items = []
        for element in elements:
            tds = element.find_elements_by_tag_name("td")
            date = tds[0].text.split("\n")[0]
            lines = tds[1].text.split("\n")
            lines_split = list(map(lambda line: line.split("   "), lines))
            transaction_name = lines_split[0][0]
            transport_type = lines_split[0][1].split(" - ")[0]
            pto = lines_split[0][1].split(" - ")[1].replace(" ", "")
            time = lines_split[1][0]
            time_object = datetime.strptime(f"{date} {time}", '%d-%m-%Y %H:%M')

            # Place at which the validator was used
            transaction_info = lines_split[1][1]
            # Get info from checkin if available, this one is only availabe at check out
            if "Check-in" in lines[2]:
                check_in_info = lines_split[2][1]
            else:
                check_in_info = None

            product_info = None
            purse_change = None
            for index, line in enumerate(lines):
                if "Product" in line:
                    product_info = lines_split[index][1]
                elif "instaptarief" in line:
                    purse_change = lines_split[index][0].replace("€ ", "").replace(",", ".").replace(" ", "")

            fare = None
            if len(tds[2].text) != 0:
                fare = tds[2].text.replace("€ ", "").replace(",", ".")

            item = {
                "checkInInfo": check_in_info,
                "fare": fare,
                "modalType": transport_type,
                "productInfo": product_info,
                "pto": pto,
                "transactionDateTime": int(time_object.timestamp() * 1000),
                "transactionInfo": transaction_info,
                "transactionName": transaction_name,
                "ePurseMut": purse_change
            }
            items.append(item)
            print(json.dumps(item))
        return items
    return None


def login(username, password):
    # Check if on login page
    try:
        username_field = driver.find_element_by_id("username")
        password_field = driver.find_element_by_id("password")
        remind_input = driver.find_element_by_id("chkRemember")
    except NoSuchElementException:
        return

    username_field.send_keys(username)
    password_field.send_keys(password)
    remind_input.click()
    driver.find_element_by_id("btn-login").click()


# Try and scrape all available pages.
def full_scrape():
    scrape("01-10-2020", "31-10-2020", 2)


driver.implicitly_wait(2)
login(LOGIN_USERNAME, LOGIN_PASSWORD)
driver.implicitly_wait(default_timeout)
full_scrape()