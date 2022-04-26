from urllib import response
from flask import Flask, render_template, request, redirect, url_for, jsonify, escape
from flask_sqlalchemy import SQLAlchemy
import json
import dynamodb.dynamoDbUtils as dynamoDbUtils
import app.models.fmwrkTables as fmwrkTables
import os
import ast
import html
from dynamodb.dynamoDbUtils import updateSourceSystem
from dynamodb.dynamoDbUtils import updateSourceSystemAsset
from scripts.setupSourceSystem import createSourceSystem
from scripts.setupSourceAsset import createSourceAsset

app = Flask(__name__,
  static_url_path='', 
  static_folder='app/static',
  template_folder='app/templates')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(os.path.join(os.path.dirname(__file__), 'sqlite/dlFmwrk.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = fmwrkTables.db
db.init_app(app)

@app.route('/test')
def test():
  data = {"bucket_name": "dl-fmwrk-10000-us-east-1",
  "data_owner": "Suprakash Nandy",
  "mechanism": "push",
  "src_sys_id": 10000,
  "src_sys_nm": "auto generated system",
  "support_cntct": "suprakash.nandy@tigeranalytics.com"}

  return render_template('test.html', title = 'Test', item = data)

@app.route('/')
def index():
  return render_template('home.html', title = 'Home')

# --------------------------------------------------------- #
# --------------- Routes for Source Systems --------------- #
# --------------------------------------------------------- #
@app.route('/sourceSystem')
def sourceSystem():
  dynamoDbUtils.scanSourceSystem()
  return render_template('sourceSystem/sourceSystem.html', title='Source System')

@app.route('/sourceSystem/data')
def sourceSystemData():
  return {'data': [source_systems.to_dict() for source_systems in fmwrkTables.sourceSystem.query]}


#@app.route('/sourceSystem/data/<int:src_sys_id_val>')
#def sourceSystemDataDetail(src_sys_id_val):
#  data = fmwrkTables.sourceSystem.query.filter_by(src_sys_id=src_sys_id_val)
#  return render_template('sourceSystem/sourceSystem.html', data = data)

# Next two routes are to edit exiting source systems
@app.route('/sourceSystem/editSource')
def sourceSystemEdit():
  src_sys_id_val = request.args.get('src_sys_id')
  result = fmwrkTables.sourceSystem.query.filter_by(src_sys_id=src_sys_id_val).all()
  for u in result:
    data = u.__dict__
  return render_template('sourceSystem/editSource.html', data = data)

@app.route('/sourceSystem/editSource/modify', methods=['POST'])
def editSrcsys():
  if request.method == "POST":
    data = json.dumps(request.json)
    response = updateSourceSystem(data)
    return jsonify({"redirect": "/sourceSystem"})

# Route is to add new source system
@app.route('/sourceSystem/createSource')
def sourceSystemCreate():
  return render_template('sourceSystem/createSource.html')

@app.route('/sourceSystem/createSource/new', methods=['POST'])
def createSrcsys():
  if request.method == "POST":
    data = json.dumps(request.json)
    response = createSourceSystem(data)
    return jsonify({"redirect": "/sourceSystem"})
# --------------------------------------------------------- #
# ----------------- End of Source Systems ----------------- #
# --------------------------------------------------------- #


# --------------------------------------------------------- #
# ----------- Routes for Source Systems Assets ------------ #
# --------------------------------------------------------- #
@app.route('/sourceSystemAsset')
def sourceSystemAsset():
  dynamoDbUtils.scanSourceSystemAsset()
  return render_template('sourceSystemAsset/sourceSystemAsset.html', title='Source System Asset')

@app.route('/sourceSystemAsset/data')
def sourceSystemAssetData():
  return {'data': [source_system_asset.to_dict() for source_system_asset in fmwrkTables.sourceSystemAsset.query]}

""" 
@app.route('/sourceSystemAsset/columnSourceAsset')
def columnSourceAsset():
  asset_id_val = request.args.get('asset_id')
  result = fmwrkTables.sourceSystemAsset.query.filter_by(asset_id=asset_id_val).all()
  for u in result:
    data = u.__dict__
  return render_template('sourceSystemAsset/columnSourceAsset.html', data = data) 
"""

@app.route('/sourceSystemAsset/columnSourceAsset')
def columnSourceAsset():
  asset_id_val = request.args.get('asset_id')
  dynamoDbUtils.scanSourceSystemAssetColumns(asset_id_val)
  dynamoDbUtils.scanSourceSystemAssetDq(asset_id_val)
  gen_asset_detail = fmwrkTables.sourceSystemAsset.query.filter_by(asset_id=asset_id_val).all()
  col_asset_detail = fmwrkTables.sourceSystemAssetColumnsFunc(asset_id_val).query.all()
  gen_asset_dq = fmwrkTables.sourceSystemAssetDqFunc(asset_id_val).query.all()

  for u in gen_asset_detail:
    gen_data = u.__dict__

  col_data = [v.__dict__ for v in col_asset_detail]
  sorted_col_data = sorted(col_data, key=lambda d: d['col_id'])
  #for v in col_asset_detail:
  #  print(v.__dict__)

  dq_data = [w.__dict__ for w in gen_asset_dq]
  
  return render_template('sourceSystemAsset/columnSourceAsset.html', gen_data=gen_data, col_data=sorted_col_data, dq_data=dq_data)

@app.route('/sourceSystemAsset/editSourceAsset')
def sourceSystemAssetEdit():
  asset_id_val = request.args.get('asset_id')
  dynamoDbUtils.scanSourceSystemAsset()
  dynamoDbUtils.scanSourceSystemAssetColumns(asset_id_val)
  dynamoDbUtils.scanSourceSystemAssetDq(asset_id_val)
  gen_asset_detail = fmwrkTables.sourceSystemAsset.query.filter_by(asset_id=asset_id_val).all()
  col_asset_detail = fmwrkTables.sourceSystemAssetColumnsFunc(asset_id_val).query.all()
  gen_asset_dq = fmwrkTables.sourceSystemAssetDqFunc(asset_id_val).query.all()

  for u in gen_asset_detail:
    gen_data = u.__dict__

  col_data = [v.__dict__ for v in col_asset_detail]
  sorted_col_data = sorted(col_data, key=lambda d: d['col_id'])
  no_of_cols = len(sorted_col_data)

  dq_data = [w.__dict__ for w in gen_asset_dq]

  return render_template('sourceSystemAsset/editSourceAsset.html', gen_data=gen_data, col_data=sorted_col_data, no_of_cols=no_of_cols, dq_data=dq_data)

@app.route('/sourceSystemAsset/editSourceAsset/modify', methods=['GET', 'POST'])
def editSrcAsset():
  if request.method == "POST":
    columnsSet = []
    dataAssetGenDet = json.dumps(json.loads(request.json['dataAssetGenDet']))
    dataAssetColDet = request.json['dataAssetColDet']
    
    for item in dataAssetColDet['columns']:
      dict_item = ast.literal_eval(item)
      columnsSet.append(dict_item)

    #finalDataAssetColDet = {"columns":columnsSet}
    response = updateSourceSystemAsset(dataAssetGenDet, dataAssetColDet)
    return jsonify({"redirect": "/sourceSystemAsset"})


@app.route('/sourceSystemAsset/createSourceAsset')
def sourceSystemAssetCreate():
  target_system = fmwrkTables.targetSystem.query.all()
  target_system_dict = [v.__dict__ for v in target_system]

  source_system = fmwrkTables.sourceSystem.query.all()
  #source_system_dict = db.session.query(fmwrkTables.sourceSystem.src_sys_id).all()
  source_system_dict = [v.__dict__ for v in source_system]

  #print("--------------" + target_system_dict["tgt_sys_id"])
  #print("--------------" + str(source_system_dict[1][0]))

  return render_template('sourceSystemAsset/createSourceAsset.html', col_data=[], target_system_dict = target_system_dict, source_system_dict = source_system_dict)


@app.route('/sourceSystemAsset/editSourceAsset/create', methods=['GET', 'POST'])
def createSrcAsset():
  if request.method == "POST":
    columnsSet = []
    dataAssetGenDet = json.dumps(json.loads(request.json['dataAssetGenDet']))
    dataAssetColDet = request.json['dataAssetColDet']
    
    for item in dataAssetColDet['columns']:
      dict_item = ast.literal_eval(item)
      columnsSet.append(dict_item)

    finalDataAssetColDet = {"columns":columnsSet}

    print("----------Columns---------" + json.dumps(dataAssetGenDet))
    response = createSourceAsset(dataAssetGenDet, json.dumps(finalDataAssetColDet))
    return jsonify({"redirect": "/sourceSystemAsset"})

if __name__ == '__main__':
  #print(sourceSystemData())
  app.run(debug=True)