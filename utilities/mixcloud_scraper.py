# Imports
import pandas as pd
import numpy as np
import re
import requests
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup as BS
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from tqdm import tqdm


# ------------------------------------------------------------------------------
# HELPER FUNCTIONS 1 ----
# ------------------------------------------------------------------------------
def get_show_info(soup, level):
    try:
        result = soup.find('span', id = level).text.strip()
    except Exception as e:
        print(f"Error: {e}")
        result = None
    return result

def get_show_tags(soup, class_name = "styles__GenreTagListItem-css-in-js__sc-j82gfl-2 jXRAOH"):
    try:
        result = soup.find_all("li", class_ = class_name)
        result = [tag.get_text(strip=True) for tag in result]
    except Exception as e:
        print(f"Error: {e}")
        result = None
    return result

def get_following_count(soup, class_name = "button__StyledChildren-css-in-js__sc-1hu2thj-1 eRIoOB"):
    following = soup.find_all("span", class_ = class_name)
    following = [span.get_text(strip=True) for span in following if 'Following' in span.get_text()]
    following = int(re.search(r'\d+', following[0]).group())
    return following

def get_follower_count(soup, class_name = "button__StyledChildren-css-in-js__sc-1hu2thj-1 eRIoOB"):
    followers = soup.find_all("span", class_ = class_name)
    followers = [span.get_text(strip=True) for span in followers if 'Followers' in span.get_text()]
    followers = int(re.search(r'\d+', followers[0].replace(',', '')).group())
    return followers

def get_show_urls(soup, class_name = "styles__PlainLink-css-in-js__sc-1d6v1iv-0 styles__TitleLink-css-in-js__sc-1d6v1iv-5 hWvYXA bQSmru"):
    show_urls = soup.find_all("a", class_ = class_name)
    show_urls = ["https://www.mixcloud.com/" + show_url['href'] for show_url in show_urls]
    return show_urls

def get_posted_date(data, column):

    df = data[[column]]

    # Mapping readable units to timedelta-supported units
    unit_map = {
        'second': 'seconds',
        'minute': 'minutes',
        'hour': 'hours',
        'day': 'days',
        'week': 'days',
        'month': 'days',
        'year': 'days'
    }

    # Multiplier to convert week/month/year to days
    multiplier_map = {
        'second': 1,
        'minute': 1,
        'hour': 1,
        'day': 1,
        'week': 7,
        'month': 30,
        'year': 365
    }

    # Step 1: Extract value and unit
    df = df \
        .assign(value=lambda x: x['date_posted'].str.extract(r'(\d+)')[0].astype('Int64')) \
        .assign(unit=lambda x: x['date_posted'].str.extract(r'(second|minute|hour|day|week|month|year)')[0]) \
        .assign(unit_mapping=lambda x: x['unit'].map(unit_map)) \
        .assign(multiplier=lambda x: x['unit'].map(multiplier_map))

    # Step 2: Safe date calculation with try/except
    df['posted_time'] = df.apply(
        lambda row: (
            datetime.now() - pd.to_timedelta(row['multiplier'], unit=row['unit_mapping'])
            if pd.notnull(row['multiplier']) and pd.notnull(row['unit_mapping'])
            else None
        ),
        axis=1
    )

    df['posted_time'] = df['posted_time'].dt.date

    return df['posted_time']


# ------------------------------------------------------------------------------
# HELPER FUNCTIONS 2 ----
# ------------------------------------------------------------------------------
# - Function to Get Chrome Browser ----
def get_chrome_driver(
    driver_path: str = '/Users/BachataLu/Desktop/School/2025_Projects/GEN_AI_EXPERIMENTS/chromedriver-mac-x64/chromedriver',
    headless: bool = True,
    dj_url: str = None,
    verbose: bool = True,
    wait_time: int = 10,
):
    """ Get Chrome Driver for Selenium Web Scraping.

    Args:
        driver_path (str, optional):
            Webdriver location. Defaults to '/Users/BachataLu/Desktop/School/2025_Projects/GEN_AI_EXPERIMENTS/chromedriver-mac-x64/chromedriver'.
        headless (bool, optional):
            Whether to use the chrome browser in headless mode. Defaults to True.
        dj_url (_type_, optional):
            Mixcould page of DJ. Defaults to "https://www.mixcloud.com/djsprenk".
    """
    # title ----
    if verbose:
        print(f"======= Scraping Info for {dj_url} ======= \n\n")

    # driver set up ----
    print("=== Step 1: Initializing Driver... ===")
    service = Service(executable_path=driver_path)
    options = webdriver.ChromeOptions()

    if headless:
        options.add_argument('--headless')
        options.add_argument('--window-size=1920,1080')
    else:
        options = options

    options.add_argument('--disable-extensions')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.page_load_strategy = 'eager'

    try:
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print(f"Error initializing Chrome driver: {e}")
        return None

    # - go to page ----
    if dj_url is None:
        print("No DJ URL provided. Please provide a valid Mixcloud DJ URL.")

    # - validate URL ----
    if not re.match(r'^https?://(www\.)?mixcloud\.com/.+', dj_url):
        print("Invalid Mixcloud URL. Please provide a valid URL.")


    # - wait for page to load ----
    try:
        driver.get(dj_url)
        wait = WebDriverWait(driver, wait_time)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'h1')))
    except TimeoutException:
        print("Timed out waiting for page to load")

    if verbose:
        print("=== Step 1 Completed: Driver Initialized ✅ === \n")

    # - return driver ----
    return driver

# Function to Scroll ----
def get_scroll_page(driver, scroll_sleep_time = 3, scroll_number = 10, verbose = True):
    """ Scroll the page to load more content.

    Args:
        driver (webdriver): Selenium WebDriver instance.
        scroll_pause_time (int, optional): Time to wait after each scroll. Defaults to 1.
        max_scrolls (int, optional): Maximum number of scrolls. Defaults to 10.
    """
    if verbose:
        print("=== Step 2: Scrolling Page... ===")

    for i in range(scroll_number):
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(scroll_sleep_time)

    if verbose:
        print("=== Step 2 Completed: Page Scrolled ✅ === \n")

    return driver

# Function to Get Page Source ----
def get_page_source(driver, verbose = True):
    """ Get the page source of the current page.

    Args:
        driver (webdriver): Selenium WebDriver instance.
        verbose (bool, optional): Whether to print verbose output. Defaults to True.
    """
    if verbose:
        print("=== Step 3: Getting Page Source... ===")

    try:
        soup = BS(driver.page_source, 'lxml')
        if verbose:
            print("=== Step 3 Completed: Page HTML Extracted ✅ === \n")

    except Exception as e:
        print(f"=== Step 2: Error Extracting Page HTML === ❌: {e}")

    return soup


# Function: Get DJ Info ----
def get_dj_info(soup, verbose = True):
    """ Get DJ Info from the page source.

    Args:
        soup (BeautifulSoup): BeautifulSoup object of the page source.
        verbose (bool, optional): Whether to print verbose output. Defaults to True.
    """
    if verbose:
        print("=== Step 4: Getting DJ Info... ===")

    try:
        dj_name = soup.find("h1", class_ = "styles__DisplayTitle-css-in-js__sc-go2u8s-3 ieRAVV").text.strip()
        dj_following = get_following_count(soup)
        dj_followers = get_follower_count(soup)
        dj_info = soup.find("div", class_ = "styles__Text-css-in-js__sc-3bsl01-4 KPhJf").text.strip()
        dj_show_urls = get_show_urls(soup)

        if verbose:
            print("=== Step 4 Completed: DJ Info Extracted ✅ === \n")

    except Exception as e:
        print(f"=== Step 4: Error Extracting DJ Info === ❌: {e}")

    return {
        'dj_name': dj_name,
        'dj_info': dj_info,
        'dj_followers': dj_followers,
        'dj_following': dj_following,
        'dj_show_urls': dj_show_urls
    }

# Function: Get Test Size ----
def get_test_size(dj_info, test_size = 2, verbose = True):
    """ Get the test size for the DJ.

    Args:
        dj_info (dict): Dictionary containing DJ info.
        test_size (int, optional): Number of shows to test. Defaults to 2.
        verbose (bool, optional): Whether to print verbose output. Defaults to True.
    """

    total_shows = len(dj_info['dj_show_urls'])
    if verbose:
        print(f"   === Total shows found: {total_shows} ===")
        if test_size > 0 and test_size < total_shows:
            print(f"   === Extracting data for {test_size} shows ===")
        else:
            print("   === Extracting data for all shows to test ===")

    return {
        'dj_name': dj_info['dj_name'],
        'dj_info': dj_info['dj_info'],
        'dj_followers': dj_info['dj_followers'],
        'dj_following': dj_info['dj_following'],
        'dj_show_urls': dj_info['dj_show_urls'][0:test_size]
    }


# Function: Get Show Info ----
def get_dj_show_info(driver, dj_info_dict_test, verbose = True):
    """ Get Show Info from the page source.

    Args:
        soup (BeautifulSoup): BeautifulSoup object of the page source.
        show_url (str): URL of the show.
        verbose (bool, optional): Whether to print verbose output. Defaults to True.
    """
    # - initialize empty list ----
    if verbose:
            print("=== Step 5: Scraping Show Info... ===")

    all_shows_data = []

    for show_url in dj_info_dict_test['dj_show_urls']:

        if verbose:
            print(f"   === Scraping data for {show_url}... ===")

        # driver
        driver.get(show_url)

        # Wait for Page to Load ----
        wait = WebDriverWait(driver, 10)

        try:
            # Wait for a key element instead of arbitrary sleep
            wait.until(EC.presence_of_element_located((By.TAG_NAME, 'h1')))
        except TimeoutException:
            print("Timed out waiting for page to load")

        # Sroll Down (Not to the End) ----
        driver.execute_script("window.scrollBy(0, 300)")

        # Click "Next" Button ----
        try:
            next_button = driver.find_element('xpath', '//*[@id="react-root"]/div[1]/div[2]/div[3]/div/div/div[1]/div/div[2]/button')
            next_button.click()
            time.sleep(0.5)
        except NoSuchElementException:
            print(f"        No next button found for {show_url}, proceeding to scrape.")
        except Exception as e:
            print(f"Warning: Error interacting with next button for {show_url}: {str(e)}")

        # Grab Page Source ----
        soup2 = BS(requests.get(show_url).text, 'html.parser')

        # Scrape Show Info ----
        show_title = soup2.find_all("h1", class_ = "wS6VZW_title E95hVG_headingMedium")[0].text.strip()
        show_plays = soup2.find_all("p", class_ = "styles__Label-css-in-js__sc-1yk6zpi-7 gdkxXY")[0].text
        show_favs = soup2.find_all("p", class_ = "styles__Label-css-in-js__sc-1yk6zpi-7 gdkxXY")[1].text
        show_posted = soup2.find_all("div", class_ = "styles__TimeSinceDesktop-css-in-js__sc-1yk6zpi-6 cwtjao")[0].get("aria-label")
        show_tags = get_show_tags(soup2)
        show_info1 = get_show_info(soup2, 'L1')
        show_info2 = get_show_info(soup2, 'L2')
        show_info3 = get_show_info(soup2, 'L3')
        show_info4 = get_show_info(soup2, 'L4')
        show_info5 = soup2.find('div', class_ = 'styles__Paragraph-css-in-js__sc-12xxm55-1 fhRopu').text.strip()

        # Append Data to List ----
        show_data = {
            'title': show_title,
            'play_count': show_plays,
            'fav_count': show_favs,
            'date_posted': show_posted,
            'show_tags': show_tags,
            'show_info1': show_info1,
            'show_info2': show_info2,
            'show_info3': show_info3,
            'show_info4': show_info4,
            'show_info5': show_info5,
            'show_url': show_url
        }

        # print("  === Appending Data to Data List... ===")
        all_shows_data.append(show_data)

    if verbose:
        # print(f"   === Data for {show_url} appended to list ✅ ===")
        print("=== Step 5 Completed: All Shows Scraped ✅ === \n")

    # - close driver ----
    driver.quit()

    # - return data ----
    return all_shows_data

# Pandas DataFrame ----
def get_dataframe(all_shows_data):
    """ Convert the list of show data to a Pandas DataFrame.

    Args:
        all_shows_data (list): List of dictionaries containing show data.
    """
    df = pd.DataFrame(all_shows_data)

    columns = [
        'name', 'title', 'show_url', 'play_count', 'fav_count', 'date_posted', 'show_tags',
        'show_info1', 'show_info2', 'show_info3', 'show_info4', 'show_info5',
    ]

    df = df.reindex(columns, axis=1)

    return df


# Format DataFrame ----
def get_formatted_dataframe(data):

    df = data.copy()

    # - format counts ----
    df['play_count'] = df['play_count'].str.replace(' plays', '').str.replace(',', '').astype(int)
    df['fav_count'] = df['fav_count'].str.replace(' favorites', '').str.replace(',', '').astype(int)

    # - data posted ----
    df['date_uploaded'] = get_posted_date(data, 'date_posted')

    # - energy ----
    energy_pattern = r'Energy\s*(\d+-\d+)\s*(?:\||and)'
    df['energy_min'] = df['show_info1'].str.extract(energy_pattern)[0].str.split('-').str[0].astype('Int64')
    df['energy_max'] = df['show_info1'].str.extract(energy_pattern)[0].str.split('-').str[1].astype('Int64')
    # df_formatted.head()

    # - bpm ----
    bpm_pattern = r'(?:\||and)\s*(\d+-\d+)\s*BPM'
    df['bpm_min'] = df['show_info1'].str.extract(bpm_pattern)[0].str.split('-').str[0].astype('Int64')
    df['bpm_max'] = df['show_info1'].str.extract(bpm_pattern)[0].str.split('-').str[1].astype('Int64')
    # df_formatted.head()

    # - tags ----
    df['show_tags_cleaned'] = df['show_tags'].apply(eval) if isinstance(df['show_tags'].iloc[0], str) else df['show_tags']
    df['show_tags_cleaned'] = df['show_tags_cleaned'] \
        .apply(
            lambda tags: ', '.join([
                re.sub(r'\d+(st|nd|rd|th)', '', tag).strip()
                    for tag in tags
                ])
            )

    # df_formatted.head()

    # - all info ----
    df['show_info_combined'] = df.apply(
        lambda row: '\n\n'.join([
            f"show_info_1:\n{row['show_info1'] if pd.notnull(row['show_info1']) else 'no info'}",
            f"show_info_2:\n{row['show_info2'] if pd.notnull(row['show_info2']) else 'no info'}",
            f"show_info_3:\n{row['show_info3'] if pd.notnull(row['show_info3']) else 'no info'}",
            f"show_info_4:\n{row['show_info4'] if pd.notnull(row['show_info4']) else 'no info'}"
        ]),
        axis=1
    )
    # df_formatted.head()

    # - column arrangement ----
    df = df[[
        'name', 'title', 'play_count', 'fav_count', 'date_posted', 'date_uploaded',
        'show_tags', 'show_tags_cleaned', 'energy_min', 'energy_max', 'bpm_min', 'bpm_max',
        'show_info1', 'show_info2', 'show_info3', 'show_info4', 'show_info5',
        'show_info_combined', 'show_url'
    ]]

    # - rename columns ----
    df = df \
        .rename(columns = {
            'show_info5': 'artists_list'
    })

    return df

# ------------------------------------------------------------------------------
# MAIN FUNCTION ----
# ------------------------------------------------------------------------------
# dj_url = 'https://www.mixcloud.com/djwarholl'
# driver_path: str = 'achataLu/Desktop/School/2025_Projects/GEN_AI_EXPERIMENTS/chromedriver-mac-x64/chromedriver'
# headless: bool = False
# wait_time: int = 11
# verbose: bool = True

def scrape_mixcloud_main(

    # driver
    driver_path: str = '/Users/BachataLu/Desktop/School/2025_Projects/mixcloud_zouk_experience/chromedriver',
    headless: bool = False,
    dj_url: str = None,
    wait_time: int = 11,
    verbose: bool = True,

    # scroll
    scroll_sleep_time: int = 3,
    scroll_number: int     = 10,

    # soup
    test_size: int = 2
):
    """_summary_

    Args:
        driver_path (str, optional): _description_. Defaults to '/Users/BachataLu/Desktop/School/2025_Projects/mixcloud_zouk_experience/chromedriver'.
        headless (bool, optional): _description_. Defaults to False.
        dj_url (str, optional): _description_. Defaults to None.
        wait_time (int, optional): _description_. Defaults to 11.
        verbose (bool, optional): _description_. Defaults to True.
        scroll_sleep_time (int, optional): _description_. Defaults to 3.
        scroll_number (int, optional): _description_. Defaults to 10.
        test_size (int, optional): An optional parameter to test by specifying the number of shows to scrape. Defaults to 2.

    Returns:
        List: Returns a list of two dataframes: DJ info and DJ shows.
    """

    main_pbar = tqdm(total=8, desc="Overall Progress", position=0, leave=True)

    # Driver ----
    chrome_driver = get_chrome_driver(
        driver_path = driver_path,
        dj_url      = dj_url,
        headless    = headless,
        wait_time   = wait_time,
        verbose     = verbose,
    )
    main_pbar.update(1)

    # Scroll ----
    scrolled_driver = get_scroll_page(
        driver            = chrome_driver,
        scroll_sleep_time = scroll_sleep_time,
        scroll_number     = scroll_number,
        verbose           = verbose
    )
    main_pbar.update(1)

    # Soup ----
    soup1 = get_page_source(driver = scrolled_driver, verbose = verbose)
    main_pbar.update(1)

    # Get DJ Info ----
    dj_info_dict = get_dj_info(soup = soup1, verbose = verbose)
    main_pbar.update(1)

    # DJ info dataframe ----
    dj_info_df = pd.DataFrame({
        'DJ Name': [dj_info_dict['dj_name']],
        'DJ Info': [dj_info_dict['dj_info']],
        'DJ Followers': [dj_info_dict['dj_followers']],
        'DJ Following': [dj_info_dict['dj_following']]
    })

    # DJ info variables ----
    name = dj_info_df['DJ Name'].values[0]

    # Get Test Size ----
    if test_size > 0:
        dj_info_dict_test = get_test_size(
            dj_info      = dj_info_dict,
            test_size    = test_size,
            verbose      = verbose
    )
    else:
        dj_info_dict_test = dj_info_dict
    main_pbar.update(1)

    # Get Show Info ----
    all_shows_data = get_dj_show_info(
        driver            = scrolled_driver,
        dj_info_dict_test = dj_info_dict_test,
        verbose           = verbose
    )
    main_pbar.update(1)

    # Append DJ Info to Show Data ----
    for show in all_shows_data:
        show['name'] = name

    # Convert to DataFrame ----
    df = get_dataframe(all_shows_data)
    main_pbar.update(1)

    # Format DataFrame ----
    dj_shows_df = get_formatted_dataframe(df)
    main_pbar.update(1)

    # Return ----
    return [dj_info_df, dj_shows_df]


# - Test the main function
# result = scrape_mixcloud_main(
#     dj_url = 'https://www.mixcloud.com/djsprenk',
#     test_size = 3,
#     headless = False,
#     verbose = True,
# )
