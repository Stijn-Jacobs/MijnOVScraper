import json
import time
from dateutil import relativedelta
from dateutil.rrule import rrule, MONTHLY
import calendar
from datetime import datetime, timedelta
import pathlib
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from settings import *
from webdriver_manager.chrome import ChromeDriverManager

# Start selenium webdriver
chrome_options = Options()
scriptDirectory = pathlib.Path().absolute()
chrome_options.add_argument(f"--user-data-dir={scriptDirectory}\\chrome-data-temp")

history_base_url = "https://www.ov-chipkaart.nl/mijn-ov-chip/mijn-ov-reishistorie.htm"
driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
driver.get(history_base_url)


def scrape(start_date, end_date, pagenum):
    formatted_end_date = end_date.strftime("%d-%m-%Y")
    formatted_start_date = start_date.strftime("%d-%m-%Y")

    print(f"Scraping: {formatted_start_date} until {formatted_end_date} page number: {pagenum}")

    driver.get(
        f"{history_base_url}?mediumid={MEDIUM_ID}&begindate={formatted_start_date}&enddate={formatted_end_date}&pagenumber={pagenum}")
    driver.implicitly_wait(4)
    elements = driver.find_elements(By.CLASS_NAME, "known-transaction")

    if len(elements) != 0:
        items = []
        for element in elements:
            tds = element.find_elements_by_tag_name("td")
            date = tds[0].text.split("\n")[0]
            lines = tds[1].text.split("\n")
            lines_split = list(map(lambda line: line.split("   "), lines))
            transaction_name = lines_split[0][0]

            transport_type = None
            pto = None
            if "Check-in" in transaction_name or "Check-uit" in transaction_name:
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
                if "Product:" in line:
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
        return items
    return None


def login(username, password):
    # Check if on login page
    try:
        username_field = driver.find_element(By.ID, "username")
        password_field = driver.find_element(By.ID, "password")
        remind_input = driver.find_element(By.ID, "chkRemember")
    except NoSuchElementException:
        return

    username_field.send_keys(username)
    password_field.send_keys(password)
    remind_input.click()
    driver.find_element(By.ID, "btn-login").click()


# Try and scrape all available pages. Until hit a certain date.
def full_scrape(until):
    items = []
    for date in [dt for dt in rrule(MONTHLY, dtstart=until, until=datetime.today())]:
        amount_of_days = calendar.monthrange(date.year, date.month)[1]
        page_num = 1
        while True:
            scraped = scrape(date, date + timedelta(days=amount_of_days - 1), page_num)
            page_num += 1
            if scraped is None or len(scraped) == 0:
                break
            else:
                items.extend(scraped)
                time.sleep(1.0)
    return items


driver.implicitly_wait(2)
login(LOGIN_USERNAME, LOGIN_PASSWORD)
driver.implicitly_wait(4)

with open('data.json', 'w') as fp:
    json.dump(full_scrape(datetime.today() - relativedelta.relativedelta(months=18)), fp)
