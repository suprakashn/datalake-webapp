from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

class sourceSystem(db.Model):
  __tablename__ = 'source_systems'
  src_sys_nm = db.Column(db.String(), primary_key=True, index=True)
  src_sys_id = db.Column(db.Integer, primary_key=True, index=True)
  mechanism = db.Column(db.Integer)
  bucket_name = db.Column(db.String(), index=True)
  data_owner = db.Column(db.String())
  support_cntct = db.Column(db.String())

  def to_dict(self):
    return {
      'src_sys_nm': self.src_sys_nm,
      'src_sys_id': self.src_sys_id,
      'mechanism': self.mechanism,
      'bucket_name': self.bucket_name,
      'data_owner': self.data_owner,
      'support_cntct': self.support_cntct
    }

class sourceSystemAsset(db.Model):
  __tablename__ = 'source_system_asset'
  asset_id = db.Column(db.Integer, primary_key=True, index=True)
  src_sys_id = db.Column(db.Integer, primary_key=True, index=True)
  target_id = db.Column(db.Integer)
  file_header = db.Column(db.String())
  multipartition = db.Column(db.String())
  file_type = db.Column(db.String())
  asset_nm = db.Column(db.String())
  subj_area_1 = db.Column(db.String())
  support_cntct = db.Column(db.String())
  trigger_file_pattern = db.Column(db.String())
  subj_area_2 = db.Column(db.String())
  asset_owner = db.Column(db.String())
  file_delim = db.Column(db.String())


  def to_dict(self):
    return {
      'asset_id': self.asset_id,
      'src_sys_id': self.src_sys_id,
      'target_id': self.target_id,
      'file_header': self.file_header,
      'multipartition': self.multipartition,
      'file_type': self.file_type,
      'asset_nm': self.asset_nm,
      'subj_area_1': self.subj_area_1,
      'support_cntct': self.support_cntct,
      'trigger_file_pattern': self.trigger_file_pattern,
      'subj_area_2': self.subj_area_2,
      'asset_owner': self.asset_owner,
      'file_delim': self.file_delim
    }

def sourceSystemAssetDqFunc(asset_id):
  tablename = "adv_dq." + str(asset_id)
  class sourceSystemAssetDq(db.Model):
    __tablename__ = tablename
    __table_args__ = {'extend_existing': True}
    dq_id = db.Column(db.String(), primary_key=True, index=True)
    dq_rule = db.Column(db.String(), primary_key=True, index=True)

    def to_dict(self):
      return {
        'dq_id': self.dq_id,
        'dq_rule': self.dq_rule
      }
  return sourceSystemAssetDq


def sourceSystemAssetColumnsFunc(asset_id):
  tablename = "data_asset." + str(asset_id)
  class sourceSystemAssetColumns(db.Model):
    __tablename__ = tablename
    __table_args__ = {'extend_existing': True}
    col_id = db.Column(db.Integer(), primary_key=True, index=True)
    col_nm = db.Column(db.String, primary_key=True, index=True)
    data_classification = db.Column(db.String)
    col_desc = db.Column(db.String())
    col_length = db.Column(db.Integer())
    req_tokenization = db.Column(db.String())
    pk_ind = db.Column(db.String())
    nullable = db.Column(db.String())
    data_type = db.Column(db.String())

    def to_dict(self):
      return {
        'col_id': self.col_id,
        'col_nm': self.col_nm,
        'data_classification': self.data_classification,
        'col_desc': self.col_desc,
        'col_length': self.col_length,
        'req_tokenization': self.req_tokenization,
        'pk_ind': self.pk_ind,
        'nullable': self.nullable,
        'data_type': self.data_type
      }
  return sourceSystemAssetColumns

class targetSystem(db.Model):
  __tablename__ = 'target_system'
  tgt_sys_id = db.Column(db.Integer(), primary_key=True, index=True)
  bucket_name = db.Column(db.String())
  domain = db.Column(db.String())
  subdomain = db.Column(db.String())
  data_owner = db.Column(db.String())
  support_cntct = db.Column(db.String())

  def to_dict(self):
    return {
      'tgt_sys_id': self.tgt_sys_id,
      'bucket_name': self.bucket_name,
      'domain': self.domain,
      'subdomain': self.subdomain,
      'data_owner': self.data_owner,
      'support_cntct': self.support_cntct
    }
