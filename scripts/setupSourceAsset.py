"""
== Create a new source system asset
1. Build the directory structure for the asset in associated S3 bucket
2. Setup creatObject event in the associated S3 bucket
3. Insert entry in the dl-fmwrk.data_asset dynamoDb table for the asset
4. Create a new dynamoDb table for the asset and create entries for all columms
"""

import sys
import os
import time
from random import random
from .commUtils import insert_asset_item_dynamoDB
from .commUtils import getGlobalParams
from .commUtils import create_asset_detail_table
from .commUtils import insert_asset_cols_dynamoDB
from .commUtils import set_bucket_event_notification
from .commUtils import create_src_s3_dir_str
from .commUtils import create_asset_catalog_table

def createSourceAsset(gen_detl, col_detl):
  asset_json_file = gen_detl
  asset_col_json_file = col_detl
  global_config = getGlobalParams()
  asset_id = int(str(random()).split(".")[1])

  print("Create asset detail table")
  create_asset_detail_table(asset_id, global_config["primary_region"])
  #create_asset_detail_table(asset_id, global_config["secondary_region"])

  print("Create asset catalog table")
  create_asset_catalog_table(asset_id, global_config["primary_region"])
  #create_asset_catalog_table(asset_id, global_config["secondary_region"])
  #time.sleep(10)

  print("Insert asset item")
  insert_asset_item_dynamoDB(asset_json_file, asset_id, global_config["primary_region"])
  #insert_asset_item_dynamoDB(asset_json_file, asset_id, global_config["secondary_region"])

  print("Insert asset columns")
  insert_asset_cols_dynamoDB(asset_col_json_file, asset_id, global_config["primary_region"])
  #insert_asset_cols_dynamoDB(asset_col_json_file, asset_id, global_config["secondary_region"])

  print("Create s3 directory structure")
  create_src_s3_dir_str(asset_id, asset_json_file, global_config["primary_region"])
  #create_src_s3_dir_str(asset_id, asset_json_file, global_config["secondary_region"])

  #print("Add Bucket Notification")
  #set_bucket_event_notification(asset_id, asset_json_file, global_config["primary_region"])
  #set_bucket_event_notification(asset_id, asset_json_file, global_config["secondary_region"])

