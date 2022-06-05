# Databricks notebook source
import datetime
import requests
from pyspark.sql import functions as F

# COMMAND ----------

def get_data(**kwargs):
    url = "https://api.opendota.com/api/proMatches"
    response = requests.get(url, params=kwargs)
    return response.json()

def get_min_match_id(df):
    min_match_id = df.select(F.min("match_id")).collect()[0][0]
    return min_match_id

def get_max_date(df):
    max_date = df.select(F.date_add(F.from_unixtime(F.max("start_time")),-1)).collect()[0][0]
    return max_date

def get_min_date(df):
    min_date = df.select(F.date_add(F.from_unixtime(F.min("start_time")),-1)).collect()[0][0]
    return min_date

def save_match_list(df):
    df.coalesce(1).write.format("json").mode("append").save("/mnt/datalake/raw/pro_matches_history")

def get_and_save(**kwargs):
    data = get_data(**kwargs) # obtem partidas novas a partir da partida mais antiga
    df = spark.createDataFrame(data) # transforma em df spark
    save_match_list(df) # salva os dados em modo append
    return df


# COMMAND ----------

def get_history_pro_matches(**kwargs):
    df = spark.read.format("json").load("/mnt/datalake/raw/pro_matches_history") # lê os dados do datalake
    min_match_id = get_min_match_id(df) # Pega partida mais antiga do nosso datalake
    
    while min_match_id is not None:
        print(min_match_id)
        try:
            df_new = get_and_save(less_than_match_id=min_match_id)
            min_match_id = get_min_match_id(df_new)
        except AnalysisException as err:
            print(err)
            break

def get_new_pro_matches(**kwargs):
    df = spark.read.format("json").load("/mnt/datalake/raw/pro_matches_history") # lê os dados do datalake
    max_date = get_max_date(df)
    
    df_new = get_and_save()
    date_process = get_min_date(df_new)
    min_match_id = get_min_match_id(df_new)

    print(min_match_id)
    while max_date <= date_process:
        df_new = get_and_save(less_than_match_id=min_match_id)
        min_match_id = get_min_match_id(df_new)

# COMMAND ----------

mode = dbutils.widgets.get("mode")

if mode == "new":
    get_new_pro_matches()
elif mode == "history":
    get_history_pro_matches()