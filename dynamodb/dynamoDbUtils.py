import boto3
import os
from dynamodb_json import json_util as djson
import json
import pandas
import sqlite3
import dynamodb
import time
from botocore.exceptions import ClientError
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String

region = 'us-east-2'
client = boto3.client('dynamodb', region_name=region)
resource = boto3.resource('dynamodb', region_name=region)
con = sqlite3.connect(os.path.join(os.path.dirname(__file__), '../sqlite/dlFmwrk.db'), check_same_thread=False)

def writeJsonFromDb(filename, dynamoDbTable, scan_kwargs):
  done = False
  start_key = None
  if os.path.exists(filename):
    os.remove(filename)

  try:
    response = client.describe_table(TableName=dynamoDbTable)
  except client.exceptions.ResourceNotFoundException:
    #Create empty json file
    df = pandas.DataFrame()
    df.to_json(filename)
  else:
    while not done:
      if start_key:
        scan_kwargs['ExclusiveStartKey'] = start_key
      response = client.scan(
        TableName=dynamoDbTable,
        Select='ALL_ATTRIBUTES'
      )

      with open(filename, "a+") as output:
        output.write(json.dumps(djson.loads(response['Items']), indent = 2))

      start_key = response.get('LastEvaluatedKey', None)
      done = start_key is None

# Function extracts source system dynamoDb records and loads into local sqlite database
def scanSourceSystem():
  scan_kwargs = { 'ProjectionExpression': "src_sys_id, bucket_name, src_sys_nm, mechanism, data_owner, support_cntct"}
  source_system_file = os.path.join(os.path.dirname(__file__), '../data/source_systems.json')
  writeJsonFromDb(source_system_file, 'dl-fmwrk.source_system', scan_kwargs)
  pd = pandas.read_json(source_system_file)
  pd.to_sql('source_systems', con, if_exists='replace', index=False)

# Function to update the source system table in dynamoDb
def updateSourceSystem(data):
  table = resource.Table('dl-fmwrk.source_system')
  record = json.loads(data)

  response = table.update_item(
    Key={
      'src_sys_id': int(record['src_sys_id']),
      'bucket_name': record['bucket_name'],
    },
    ConditionExpression="attribute_exists(src_sys_id)",
    UpdateExpression='SET data_owner = :val1, src_sys_nm = :val2, support_cntct = :val3',
    ExpressionAttributeValues = {
      ':val1': record['data_owner'],
      ':val2': record['src_sys_nm'],
      ':val3': record['support_cntct'],
    }
  )
  scanSourceSystem()
  return response

# Function extracts source system asset dynamoDb records and loads into local sqlite database
def scanSourceSystemAsset():
  scan_kwargs = { 'ProjectionExpression': "asset_id, src_sys_id, target_id, file_header, \
                    multipartition, file_type, asset_nm, subj_area_1, support_cntct, \
                    trigger_file_pattern, subj_area_2, asset_owner, file_delim" }

  source_system_asset_file = os.path.join(os.path.dirname(__file__), '../data/source_system_asset.json')
  writeJsonFromDb(source_system_asset_file, 'dl-fmwrk.data_asset', scan_kwargs)
  pd = pandas.read_json(source_system_asset_file)

  # Change boolean to string
  mask = pd.applymap(type) != bool
  d = {True: 'True', False: 'False'}
  pd = pd.where(mask, pd.replace(d))

  pd.to_sql('source_system_asset', con, if_exists='replace', index=False)

#def createAssetColumnsTable(tableName):
#  #engine = create_engine(os.path.join('sqlite://', os.path.dirname(__file__), '../sqlite/dlFmwrk.db'), echo=True)
#  engine = create_engine('sqlite:////mnt/d/Data/solaris/python_workspace/myPython/datalake-webapp/sqlite/dlFmwrk.db', echo=True)
#
#  #if not engine.dialect.has_table(engine, tableName):
#  metadata = MetaData()
#  Table(tableName, metadata,
#    Column('col_id', Integer, primary_key=True, nullable=False),
#    Column('col_nm', String, primary_key=True, nullable=False),
#    Column('data_classification', String),
#    Column('col_desc', String),
#    Column('col_length', Integer),
#    Column('req_tokenization', String),
#    Column('pk_ind', String),
#    Column('nullable', String),
#    Column('data_type', String)
#  )
#  metadata.create_all(engine)

def scanSourceSystemAssetColumns(asset_id):
  dynamoDBtableName = "dl-fmwrk.data_asset." + str(asset_id)
  sqlitetableName = "data_asset." + str(asset_id)
  #createAssetColumnsTable(sqlitetableName)

  scan_kwargs = { 'ProjectionExpression': "col_id, col_nm, data_classification, col_desc, \
                    col_length, req_tokenization, pk_ind, 'nullable', data_type" }

  source_system_asset_columns_file = os.path.join(os.path.dirname(__file__), '../data/asset_columns.{}.json'.format(asset_id))
  writeJsonFromDb(source_system_asset_columns_file, dynamoDBtableName, scan_kwargs)
  pd = pandas.read_json(source_system_asset_columns_file)
  # Change boolean to string
  mask = pd.applymap(type) != bool
  d = {True: 'True', False: 'False'}
  pd = pd.where(mask, pd.replace(d))
  print(pd)
  pd.to_sql(sqlitetableName, con, if_exists='replace', index=False)


def updateSourceSystemAssetDq(dataAssetGenDet, asset_id):
  dynamoDBtableName = "dl-fmwrk.adv_dq." + str(asset_id)
  adv_dq = dataAssetGenDet["adv_dq"].splitlines()
  if not adv_dq:
    try:
      response = client.describe_table(TableName=dynamoDBtableName)
    except client.exceptions.ResourceNotFoundException:
      return 0
    else:
      # Drop the table
      client.delete_table(TableName=dynamoDBtableName)
      #dynamoDBtableName.delete()
  else:
    adv_dq_dict = {"adv_dq_rules": []}
    count = 0
  
    for v in adv_dq:
      dq_dict_item = {"dq_id": str(asset_id) + "_" + str(count), "asset_id": asset_id, "dq_rule": v}
      adv_dq_dict["adv_dq_rules"].append(dq_dict_item)
      count = count + 1

    try:
      response = client.describe_table(TableName=dynamoDBtableName)

    except client.exceptions.ResourceNotFoundException:
      print("The DQ table does not exit!!!")

    else:
      # Drop the existing DQ table
      response = client.delete_table(TableName=dynamoDBtableName)
      time.sleep(10)
      print(response)

    finally:
      #Create the table & insert records
      print('Creating the table {} in {}'.format(dynamoDBtableName, region))
      asset_dq_table = client.create_table(
        TableName=dynamoDBtableName,
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

      print('Inserting DQ rules in the table {} in {}'.format(dynamoDBtableName, region))
      for rows in adv_dq_dict["adv_dq_rules"]:
        item = json.dumps(rows)
        jsonItem = json.loads(item)
        asset_dq_table = resource.Table(dynamoDBtableName)
        response = asset_dq_table.put_item(Item=jsonItem)
  
# Function to update the source system asset in dynamoDb
def updateSourceSystemAsset(dataAssetGenDet, dataAssetColDet):
  dataAssetGenDet = json.loads(dataAssetGenDet)
  asset_id = dataAssetGenDet["asset_id"]

  table = resource.Table("dl-fmwrk.data_asset")
  response = table.update_item(
    Key={
      'asset_id': int(asset_id),
      'src_sys_id': int(dataAssetGenDet["src_sys_id"]),
    },
    ConditionExpression="attribute_exists(asset_id)",
    UpdateExpression='SET file_type = :val1, subj_area_1 = :val2, subj_area_2 = :val3, asset_nm = :val4, file_header = :val5, support_cntct = :val6, asset_owner = :val7, file_delim = :val8',
    ExpressionAttributeValues = {
      ':val1': dataAssetGenDet['file_type'],
      ':val2': dataAssetGenDet['subj_area_1'],
      ':val3': dataAssetGenDet['subj_area_2'],
      ':val4': dataAssetGenDet['asset_nm'],
      ':val5': dataAssetGenDet['file_header'],
      ':val6': dataAssetGenDet['support_cntct'],
      ':val7': dataAssetGenDet['asset_owner'],
      ':val8': dataAssetGenDet['file_delim'],
    }
  )

  table = resource.Table("dl-fmwrk.data_asset." + str(asset_id))
  print(dataAssetColDet)
  for column_string in dataAssetColDet["columns"]:
    column = json.loads(column_string)
    response = table.update_item(
      Key={
        'col_id': int(column['col_id']),
        'col_nm': column['col_nm'],
      },
      ConditionExpression="attribute_exists(col_id)",
      UpdateExpression='SET col_desc = :val1, pk_ind = :val2, col_length = :val3, nullable = :val4',
      ExpressionAttributeValues = {
        ':val1': column['col_desc'],
        ':val2': column['pk_ind'],
        ':val3': column['col_length'],
        ':val4': column['nullable'],
      }
    )
  updateSourceSystemAssetDq(dataAssetGenDet, asset_id)
  scanSourceSystemAsset()
  scanSourceSystemAssetColumns(asset_id)
  scanSourceSystemAssetDq(asset_id)
  return response

# Function extracts source asset DQ dynamoDb records and loads into local sqlite database
def scanSourceSystemAssetDq(asset_id):
  dynamoDBtableName = "dl-fmwrk.adv_dq." + str(asset_id)
  sqlitetableName = "adv_dq." + str(asset_id)
  scan_kwargs = { 'ProjectionExpression': "dq_id, dq_rule"}
  source_system_asset_dq_file = os.path.join(os.path.dirname(__file__), '../data/asset_dq_rules.{}.json'.format(asset_id))
  writeJsonFromDb(source_system_asset_dq_file, dynamoDBtableName, scan_kwargs)
  pd = pandas.read_json(source_system_asset_dq_file)
  #con.execute("DELETE FROM '{}'".format(sqlitetableName))
  if not pd.empty:
    pd.to_sql(sqlitetableName, con, if_exists='replace', index=False)
  else:
    con.execute("CREATE TABLE IF NOT EXISTS '{}' (dq_rule, dq_id, asset_id)".format(sqlitetableName))