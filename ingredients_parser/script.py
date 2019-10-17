#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import ast
import json
import config
import numpy as np
import pandas as pd
import requests as r
from SpoonacularAPI import spoonacular as sp  # to make api call to spoonacular api
import snowflake.connector  # call database


# pull in data from snowflake
def get_query(snowflake_query):
    # connecting to snowflake db
    con = snowflake.connector.connect(
        user=config.user_name,
        password=config.user_passwd,
        account=config.user_acc,
        role=config.user_role,
        warehouse=config.user_wh,
        database=config.user_db,
        schema=config.user_schema
    )
    # writing data to pandas df
    data = pd.read_sql(query, con)
    # closing connection
    con.close()
    # returns df
    return data


query = """
SELECT *
FROM "USER"."TKEOUGH"."ALL_COOKIE_SAMPLE_CLONE";
"""

results = get_query(query)


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


def parse_ingredients(url, ingredients_data):
    api = sp.API(config.spoonacular_api_key)
    api_res = api.parse_ingredients(ingredients_data, servings=1)
    data = api_res.json()
    write_to_files('parsed_ingredients.csv', [url, ingredients_data, data])
    return url, ingredients_data, data


# loop through dataset
for index, row in results.iterrows():
    u = row['URL_SUB_PAGE']
    i = row['INGREDIENT_LIST_CLEAN']
    # run ally method on ingredients lst to format them for api

    parsed = parse_ingredients(u, i)
    print(parsed)


# read in master parsed file
df = pd.read_csv('parsed_ingredients.csv')


# process data set
df['response'] = df['response'].apply(ast.literal_eval)
df_2 = df.explode('response')
# df_2 = df_2['response'].apply(pd.Series)
df_2 = pd.concat([df_2.drop(['response'], axis=1), df_2['response'].apply(pd.Series)], axis=1)

df_2.to_csv('final_parsed_data_set.csv')