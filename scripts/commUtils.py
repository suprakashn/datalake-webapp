import json
import decimal
import time
import sys
import os
import random
import boto3


def getGlobalParams():
    script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
    gbl_cfg_rel_path = "../config/globalConfig.json"
    gbl_cfg_abs_path = os.path.join(script_dir, gbl_cfg_rel_path)

    with open(gbl_cfg_abs_path) as json_file:
        global_config = json.load(json_file)
        return global_config


def create_insert_asset_dq(adv_dq_dict, asset_id, region):
    dynamodb = boto3.resource('dynamodb', region_name = region)
    global_config = getGlobalParams()

    print('Creating the table {}.adv_dq.{} in {}'.format(global_config["fm_prefix"], str(asset_id), region))
    asset_dq_table = dynamodb.create_table(
      TableName=global_config["fm_prefix"] + ".adv_dq." + str(asset_id),
      KeySchema=[
        {
          'AttributeName': 'dq_id',
          'KeyType': 'HASH'
        },
      ],
      AttributeDefinitions=[
        {
          'AttributeName': 'dq_id',
          'AttributeType': 'S'
        },
      ],
      ProvisionedThroughput={
        'ReadCapacityUnits': 1,
        'WriteCapacityUnits': 1,
      }
    )
    time.sleep(10)

    print(
        "Inserting column info in {}.adv_dq.{} table in {}".format(
            global_config["fm_prefix"], asset_id, region
        )
    )
    for rows in adv_dq_dict["adv_dq_rules"]:
        item = json.dumps(rows)
        jsonItem = json.loads(item)
        asset_dq_table = dynamodb.Table(
            "{}.adv_dq.{}".format(global_config["fm_prefix"], asset_id)
        )
        response = asset_dq_table.put_item(Item=jsonItem)


def insert_asset_item_dynamoDB(asset_json_file, asset_id, region):
    dynamodb = boto3.resource("dynamodb", region_name=region)
    global_config = getGlobalParams()

    asset_config = json.loads(asset_json_file)

    # Remove advanced dq rules from asset_config dict and create new dict for it
    adv_dq = asset_config["adv_dq"].splitlines()
    adv_dq_dict = {"adv_dq_rules": []}
    count = 0
    
    for v in adv_dq:
        dq_dict_item = {"dq_id": str(asset_id) + "_" + str(count), "dq_rule": v}
        adv_dq_dict["adv_dq_rules"].append(dq_dict_item)
        count = count + 1
    asset_config.pop("adv_dq")

    print(type(adv_dq_dict["adv_dq_rules"]))

    # Create advance dq table and insert rules (if there are rules defined)
    if adv_dq_dict["adv_dq_rules"]:
        create_insert_asset_dq(adv_dq_dict, asset_id, region)

    asset_config.update({"asset_id": asset_id})
    item = json.dumps(asset_config)

    asset_table = dynamodb.Table("{}.data_asset".format(global_config["fm_prefix"]))
    jsonItem = json.loads(item)

    jsonItem["src_sys_id"] = int(jsonItem["src_sys_id"])
    jsonItem["target_id"] = int(jsonItem["target_id"])
    for key, val in jsonItem.items():
        if val == 'true':
            val = True
        elif val == 'false':
            val = False

    print(
        "Inserting {} info in {}.data_asset table in {}".format(
            asset_id, global_config["fm_prefix"], region
        )
    )
    response = asset_table.put_item(Item=jsonItem)


def insert_asset_cols_dynamoDB(asset_col_json_file, asset_id, region):
    dynamodb = boto3.resource("dynamodb", region_name=region)
    global_config = getGlobalParams()

    asset_col_config = json.loads(asset_col_json_file)

    for listItem in asset_col_config["columns"]:
        listItem["col_id"] = int(listItem["col_id"])
        listItem["col_length"] = 0 if not listItem["col_length"] else int(listItem["col_length"])
        for key, val in listItem.items():
            if val == 'true':
                val = True
            elif val == 'false':
                val = False

    print(asset_col_config)
    print(
        "Inserting column info in {}.data_asset.{} table in {}".format(
            global_config["fm_prefix"], asset_id, region
        )
    )
    for rows in asset_col_config["columns"]:
        item = json.dumps(rows)
        jsonItem = json.loads(item)
        asset_col_table = dynamodb.Table(
            "{}.data_asset.{}".format(global_config["fm_prefix"], asset_id)
        )
        response = asset_col_table.put_item(Item=jsonItem)


def create_asset_catalog_table(asset_id, region):
  dynamodb = boto3.resource('dynamodb', region_name = region)
  global_config = getGlobalParams()

  print('Creating the table {}.data_catalog.{} in {}'.format(global_config["fm_prefix"], str(asset_id), region))
  asset_detail_table = dynamodb.create_table(
    TableName=global_config["fm_prefix"] + ".data_catalog." + str(asset_id),
    KeySchema=[
      {
        'AttributeName': 'exec_id',
        'KeyType': 'HASH'
      },
    ],
    AttributeDefinitions=[
      {
        'AttributeName': 'exec_id',
        'AttributeType': 'S'
      },
    ],
    ProvisionedThroughput={
      'ReadCapacityUnits': 1,
      'WriteCapacityUnits': 1,
    }
  )


def create_asset_detail_table(asset_id, region):
    dynamodb = boto3.resource("dynamodb", region_name=region)
    global_config = getGlobalParams()

    print(
        "Creating the table {}.data_asset.{} in {}".format(
            global_config["fm_prefix"], str(asset_id), region
        )
    )
    asset_detail_table = dynamodb.create_table(
        TableName=global_config["fm_prefix"] + ".data_asset." + str(asset_id),
        KeySchema=[
            {"AttributeName": "col_id", "KeyType": "HASH"},
            {"AttributeName": "col_nm", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "col_id", "AttributeType": "N"},
            {"AttributeName": "col_nm", "AttributeType": "S"},
        ],
        ProvisionedThroughput={
            "ReadCapacityUnits": 1,
            "WriteCapacityUnits": 1,
        },
    )


def create_src_s3_dir_str(asset_id, asset_json_file, region):
    global_config = getGlobalParams()
    asset_config = json.loads(asset_json_file)

    src_sys_id = asset_config["src_sys_id"]
    bucket_name = global_config["fm_prefix"] + "-" + str(src_sys_id) + "-" + region

    print("Creating directory structure in {} bucket".format(bucket_name))
    os.system(
        'aws s3api put-object --bucket "{}" --key "{}/init/dummy"'.format(
            bucket_name, asset_id
        )
    )
    os.system(
        'aws s3api put-object --bucket "{}" --key "{}/error/dummy"'.format(
            bucket_name, asset_id
        )
    )
    os.system(
        'aws s3api put-object --bucket "{}" --key "{}/masked/dummy"'.format(
            bucket_name, asset_id
        )
    )
    os.system(
        'aws s3api put-object --bucket "{}" --key "{}/error/dummy"'.format(
            bucket_name, asset_id
        )
    )
    os.system(
        'aws s3api put-object --bucket "{}" --key "{}/logs/dummy"'.format(
            bucket_name, asset_id
        )
    )


def set_bucket_event_notification(asset_id, asset_json_file, region):
    global_config = getGlobalParams()
    with open(asset_json_file) as json_file:
        asset_config = json.load(json_file)

    src_sys_id = asset_config["src_sys_id"]
    bucket_name = global_config["fm_prefix"] + "-" + str(src_sys_id) + "-" + region
    key_prefix = str(asset_id) + "/init/"
    if asset_config["multipartition"] == False:
        key_suffix = asset_config["file_type"]
    else:
        key_suffix = asset_config["trigger_file_pattern"]

    s3_event_name = str(asset_id) + "-createObject"
    sns_name = (
        global_config["fm_prefix"] + "-" + str(src_sys_id) + "-init-file-creation"
    )
    sns_arn = (
        "arn:aws:sns:" + region + ":" + global_config["aws_account"] + ":" + sns_name
    )
    s3Client = boto3.client("s3")

    print("Creating putObject event notification to {} bucket".format(bucket_name))
    s3Client.put_bucket_notification_configuration(
        Bucket=bucket_name,
        NotificationConfiguration={
            "TopicConfigurations": [
                {
                    "Id": s3_event_name,
                    "TopicArn": sns_arn,
                    "Events": ["s3:ObjectCreated:*"],
                    "Filter": {
                        "Key": {
                            "FilterRules": [
                                {"Name": "prefix", "Value": key_prefix},
                                {"Name": "suffix", "Value": key_suffix},
                            ]
                        }
                    },
                }
            ]
        },
    )
