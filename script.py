#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import csv
import sys
import time
import config
import platform
import datetime
import numpy as np
import pandas as pd
import requests as r
from random import randint
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

# setting random headers
ua = UserAgent().random
headers = {"User-Agent": ua, "referer": "no-referrer-when-downgrade"}


def write_to_files(file, vars_):
    """
    function used to write to file
    takes in file name, and list or tuple
    that is being written
    """
    with open(file, 'a') as f:
        writer = csv.writer(f)
        # vars has to be list or tuple
        writer.writerow(vars_)
    f.close


def _find_chromedriver():
    """Function to find the chrome driver executable for selenium.
    Returns:
        String -- Absolute file path.
    """

    if platform.system() == 'Windows':
        directory = 'c:\\'
        driver = 'chromedriver.exe'
    else:
        directory = '/'
        driver = 'chromedriver'
    for root, dirs, files in os.walk(directory):
        for name in files:
            if name == driver:
                driver_path = os.path.abspath(os.path.join(root, name))
                return driver_path
    return sys.exit('Chrome driver not found, please download chrome driver before proceeding.')


def simple_get_request(endpoint):
    """
    attempts to make a connection to retrieve url content
    if connection unsuccessful None object returned
    """
    try:
        res = r.get(endpoint, headers=headers, timeout=15)
        raw_html = res.content
    except r.exceptions.RequestException as e:  # storing error in e var
        return None
    return raw_html


def proxied_request(rec_endpoint):
    # crawler configuration
    proxy_auth = config.crawlera_key  # Make sure to include ':' at the end
    proxy_host = "proxy.crawlera.com"
    proxy_port = "8010"
    proxies = {"https": "https://{}@{}:{}/".format(proxy_auth, proxy_host, proxy_port),
               "http": "http://{}@{}:{}/".format(proxy_auth, proxy_host, proxy_port)}
    try:
        req = r.get(rec_endpoint, proxies=proxies, verify=False, headers=headers, timeout=15)
        raw_html = req.content
    except r.exceptions.RequestException as e:  # storing error in e var
        return None
    return raw_html


def pages_to_crawl_df():
    url_lst = []
    for i in range(1, 260):
        temp_dict = {}
        new_url = f"https://www.allrecipes.com/recipes/362/desserts/cookies/?page={i}"
        page_number = f'page {i} of 259'
        temp_dict['page_url'] = new_url
        temp_dict['page'] = page_number
        url_lst.append(temp_dict)
    # make lst into df
    return pd.DataFrame(url_lst)


def parse_cards(end_p, page_meta):
    # Create selenium chrome driver instance.
    driver = _find_chromedriver()
    options = Options()
    options.add_argument('--no-proxy-server')
    options.headless = True
    driver = webdriver.Chrome(driver, options=options)
    print('requesting html..', end_p)
    driver.get(end_p)
    time.sleep(randint(4, 8))
    soup = BeautifulSoup(driver.page_source.encode('utf-8'), "html.parser")
    # grab cards
    cards = soup.find_all('article', {'class': 'fixed-recipe-card'})
    all_links_data = []
    for card in cards:
        temp_group = []
        temp_group.append(end_p)
        temp_group.append(page_meta)
        try:
            rec_url = card.h3.a['href']
        except:
            rec_url = 'NO_URL'
        temp_group.append(rec_url)
        all_links_data.append(temp_group)
    return all_links_data


def parse_recipes(page_e, page_i, rec_endpoint):
    # Create selenium chrome driver instance.
    driver = _find_chromedriver()
    options = Options()
    options.add_argument('--no-proxy-server')
    options.headless = True
    driver = webdriver.Chrome(driver, options=options)
    print('requesting html..', rec_endpoint)
    driver.get(rec_endpoint)
    time.sleep(randint(3, 6))
    #gather data points from recipies
    if rec_endpoint is not None:
        soup = BeautifulSoup(driver.page_source.encode('utf-8'), "html.parser")
        try:
            cookie_name = soup.select_one('h1#recipe-main-content').get_text()
        except:
            cookie_name = 'no_cookie_name'
        try:
            rating = soup.select_one('div.rating-stars')['data-ratingstars']
        except:
            rating = 'error_getting_rating'
        try:
            total_made_it = soup.select_one('div.total-made-it').get_text()
        except:
            total_made_it = 'error_getting_total_made_it'
        try:
            ready_in_time = soup.select_one('span.ready-in-time').get_text()
        except:
            ready_in_time = 'error_getting_ready_in_time'
        try:
            serving_count = soup.select_one('span.servings-count').get_text()
        except:
            serving_count = 'error_getting_serving_count'
        try:
            cal_count = soup.select_one('span.calorie-count').get_text()
        except:
            cal_count = 'error_getting_cal_count'
        try:
            ing_lst = soup.find_all('span', {'class': 'recipe-ingred_txt'})
            clean_ing = [i.get_text() for i in ing_lst]
            ing_lst = clean_ing
        except:
            ing_lst = 'error_getting_ingredients'
        try:
            prep_items = soup.find_all('li', {'class': 'prepTime__item'})
            clean_prep = [i.get_text() for i in prep_items]
            prep_items = clean_prep
        except:
            prep_items = 'error_getting_prep_items'
        try:
            dir_steps = soup.find_all('span', {'class': 'recipe-directions__list--item'})
            clean_dir_steps = [i.get_text() for i in dir_steps]
            dir_steps = clean_dir_steps
        except:
            dir_steps = 'error_getting_steps'
        # write to csv
        write_to_files('cookie_data.csv', [page_e, page_i, rec_endpoint, cookie_name, rating, total_made_it, ready_in_time, serving_count, cal_count, ing_lst, prep_items, dir_steps])
    else:
        write_to_files('error_cookie_data.csv', [page_e, page_i, rec_endpoint])
    driver.close()


# def parse_recipes(meta1, meta2, meta3, rec_html):
#     if rec_html is not None:
#         soup = BeautifulSoup(rec_html, "html.parser")
#         try:
#             cookie_name = soup.select_one('h1#recipe-main-content').get_text()
#         except:
#             cookie_name = 'no_cookie_name'
#         try:
#             rating = soup.select_one('div.rating-stars')['data-ratingstars']
#         except:
#             rating = 'error_getting_rating'
#         try:
#             total_made_it = soup.select_one('div.total-made-it').get_text()
#         except:
#             total_made_it = 'error_getting_total_made_it'
#         try:
#             ready_in_time = soup.select_one('span.ready-in-time').get_text()
#         except:
#             ready_in_time = 'error_getting_ready_in_time'
#         try:
#             serving_count = soup.select_one('span.servings-count').get_text()
#         except:
#             serving_count = 'error_getting_serving_count'
#         try:
#             cal_count = soup.select_one('span.calorie-count').get_text()
#         except:
#             cal_count = 'error_getting_cal_count'
#         try:
#             ing_lst = soup.find_all('span', {'class': 'recipe-ingred_txt'})
#             clean_ing = [i.get_text() for i in ing_lst]
#             ing_lst = clean_ing
#         except:
#             ing_lst = 'error_getting_ingredients'
#         try:
#             prep_items = soup.find_all('li', {'class': 'prepTime__item'})
#             clean_prep = [i.get_text() for i in prep_items]
#             prep_items = clean_prep
#         except:
#             prep_items = 'error_getting_prep_items'
#         try:
#             dir_steps = soup.find_all('span', {'class': 'recipe-directions__list--item'})
#             clean_dir_steps = [i.get_text() for i in dir_steps]
#             dir_steps = clean_dir_steps
#         except:
#             dir_steps = 'error_getting_steps'
#         # write to csv
#         write_to_files('cookie_data.csv', [meta1, meta2, meta3, cookie_name, rating, total_made_it, ready_in_time, serving_count, cal_count, ing_lst, prep_items, dir_steps])
#     else:
#         write_to_files('error_cookie_data.csv', [meta1, meta2, meta3])

# # endpoints data frame
# card_endpoints_df = pages_to_crawl_df()
# # write to csv
# card_endpoints_df.to_csv('card_endpoints.csv', index=False)
#
# # master links list
# links_ = []
# # looping through df
# for index, row in card_endpoints_df.iterrows():
#     p_num = row["page"]
#     endp = row["page_url"]
#     data = parse_cards(endp, p_num)
#     links_.extend(data)
#
# # df of links
# rec_links_df = pd.DataFrame(links_)
# write to csv
# rec_links_df.to_csv('cookie_recipe_endpoints.csv', index=False)

# read in
rec_links_df = pd.read_csv('cookie_recipe_endpoints.csv')

# set column names
rec_links_df.rename(columns={'0': 'PAGE_ENDPOINT', '1': "PAGE_INFO", '2': 'REC_ENDPOINT'}, inplace=True)

# filter and remove all columns with no endpoint
Final_df = rec_links_df[rec_links_df.REC_ENDPOINT != 'NO_URL']


for index, row in Final_df.iterrows():
    p_ = row['PAGE_ENDPOINT']
    i_ = row['PAGE_INFO']
    r_ = row['REC_ENDPOINT']
    # parse cookie recipe and writing results to csv file
    parse_recipes(p_, i_, r_)

