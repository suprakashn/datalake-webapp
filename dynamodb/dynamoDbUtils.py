import boto3
import os
from dynamodb_json import json_util as djson
import json
import pandas
import sqlite3
import dynamodb
from botocore.exceptions import ClientError
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String

client = boto3.client('dynamodb', region_name='us-east-2')
resource = boto3.resource('dynamodb', region_name='us-east-2')
con = sqlite3.connect(os.path.join(os.path.dirname(__file__), '../sqlite/dlFmwrk.db'), check_same_thread=False)

def writeJsonFromDb(filename, dynamoDbTable, scan_kwargs):
  done = False
  start_key = None
  if os.path.exists(filename):
    os.remove(filename)

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

def createAssetColumnsTable(tableName):
  #engine = create_engine(os.path.join('sqlite://', os.path.dirname(__file__), '../sqlite/dlFmwrk.db'), echo=True)
  engine = create_engine('sqlite:////mnt/d/Data/solaris/python_workspace/myPython/datalake-webapp/sqlite/dlFmwrk.db', echo=True)

  #if not engine.dialect.has_table(engine, tableName):
  metadata = MetaData()
  Table(tableName, metadata,
    Column('col_id', Integer, primary_key=True, nullable=False),
    Column('col_nm', String, primary_key=True, nullable=False),
    Column('data_classification', String),
    Column('col_desc', String),
    Column('col_length', Integer),
    Column('req_tokenization', String),
    Column('pk_ind', String),
    Column('nullable', String),
    Column('data_type', String)
  )
  metadata.create_all(engine)

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
  pd.to_sql(sqlitetableName, con, if_exists='replace', index=False)


# Function to update the source system asset in dynamoDb
def updateSourceSystemAsset(dataAssetGenDet, dataAssetColDet):
  dataAssetGenDet = json.loads(dataAssetGenDet)
  #dataAssetColDet = json.loads(dataAssetColDet)

  print(dataAssetColDet)
  print(dataAssetGenDet["asset_id"])


#  table = resource.Table("dl-fmwrk.data_asset." + str(asset_id))
#  response = table.update_item(
#    Key={
#      'src_sys_id': int(record['src_sys_id']),
#      'bucket_name': record['bucket_name'],
#    },
#    ConditionExpression="attribute_exists(src_sys_id)",
#    UpdateExpression='SET data_owner = :val1, src_sys_nm = :val2, support_cntct = :val3',
#    ExpressionAttributeValues = {
#      ':val1': record['data_owner'],
#      ':val2': record['src_sys_nm'],
#      ':val3': record['support_cntct'],
#    }
#  )
#  return response