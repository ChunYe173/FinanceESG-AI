import sqlite3
from datetime import date
import streamlit as st

import pandas as pd
import os


class DocumentStoreDAL:
    """
    Provides methods to retrieve Document related information from the Document Store.
    This class is for use within a Streamlit application and makes use of the Streamlit connection library
    """

    def __init__(self):
        #self.ds_conn = st.experimental_connection("document_store", "sql")
        self.ds_conn = st.connection("document_store", "sql")

    def get_organisation_id_name(self):
        # load all company names from DB
        sql = f"SELECT  id, name FROM organisations"
        df = self.ds_conn.query(sql)
        return df
    def get_country(self, org_id):
        # load all company names from DB
        sql = f"SELECT country FROM organisations WHERE id ={org_id}"
        df = self.ds_conn.query(sql)
        return df
    
    def get_document(self, doc_id: int):
        # Load from Document Store DB
        sql = f"SELECT * FROM documents WHERE id = {doc_id}"
        df = self.ds_conn.query(sql)
        return df

    def get_document_content(self, doc_id: int):
        # Load from Document Store DB
        sql = f"SELECT document_part_content FROM document_parts WHERE document_id = {doc_id} order by document_part_idx"
        df = self.ds_conn.query(sql)
        return df

    def get_esg_data(self, org_id: int):
        # Load esg data from Document Store DB
        sql = f"SELECT * FROM organisations_esg_scores WHERE org_id = {org_id} "
        df = self.ds_conn.query(sql)
        return df
    
    def get_green_washing_score(self, org_id: int):
        # Load green washing score from Document Store DB
        # sql = f"select AVG(greenwashing_score) as avg_gw from document_parts where document_id in (select id from documents where org_id = {org_id})"
        sql = f"SELECT AVG(score) as avg_gw FROM document_part_scores"
        sql += f" WHERE document_id in (SELECT id from documents WHERE org_id ={org_id}) and score_type = 'greenwashing'"

        df = self.ds_conn.query(sql)
        return df
    def get_digital_identity_score(self, org_id: int):
        # Load digital identity score from Document Store DB
        sql = f"SELECT score FROM organisations_di_scores"
        sql += f" WHERE org_id = {org_id} and score_type = 'digital_score'"
        sql += f" ORDER BY timestamp DESC"
        sql += f" LIMIT 1"
        df = self.ds_conn.query(sql)
        return df
    def get_ws_rank(self, org_id: int):
        # Load ws rank from Document Store DB
        sql = f"SELECT score FROM organisations_di_scores"
        sql += f" WHERE org_id = {org_id} and score_type = 'ws_rank'"
        sql += f" ORDER BY timestamp"
        sql += f" LIMIT 1"
        df = self.ds_conn.query(sql)
        return df
    def get_licence_info(self, org_id:int):
        sql = f"select certifier, licence_state from organisation_licences where org_id = {org_id}"
        df = self.ds_conn.query(sql)
        return df

    def get_org_sentiment_timeline(self, org_id: int, start_date: date = None, end_date: date = None) -> pd.DataFrame:
        # Load from Document Store DB
        sql = f"SELECT * FROM documents WHERE org_id = {org_id}"
        if start_date is not None:
            sql += f" and timestamp >= '{start_date.strftime('%Y-%m-%d')}'"
        if end_date is not None:
            sql += f" and timestamp <= '{end_date.strftime('%Y-%m-%d')}'"
        df = self.ds_conn.query(sql)
        return df
    
    def get_sentiment_document_chunks(self, org_id:int,start_date: date = None, end_date: date = None):
        # load sentiment data from Document Store DB
        
        sql = f"select dp.document_id, d.source_url, d.timestamp, dp.esg_category, dps.score as sentiment"
        sql += f" from document_part_scores dps"
        sql += f" left join document_parts dp"
        sql += f" on dps.document_id = dp.document_id and dps.document_part_idx = dp.document_part_idx"
        sql += f" LEFT JOIN documents d ON d.id = dps.document_id"
        sql += f" where org_id = {org_id} and dps.score_type = 'sentiment' and dp.esg_category != 'Non-ESG'"

        if start_date is not None:
            sql += f" and timestamp >= '{start_date.strftime('%Y-%m-%d')}'"
        if end_date is not None:
            sql += f" and timestamp <= '{end_date.strftime('%Y-%m-%d')}'"
        df = self.ds_conn.query(sql)
        return df
        

    def get_org_controversy_timeline(self, org_id: int, start_date: date = None, end_date: date = None) -> pd.DataFrame:
        # Load from Document Store DB
        sql = (f"SELECT documents.id as doc_id, documents.timestamp, document_controversy.*  FROM documents " +
               "INNER JOIN document_controversy ON documents.id = document_controversy.document_id " +
               f"WHERE documents.org_id = {org_id}")
        if start_date is not None:
            sql += f" and documents.timestamp >= '{start_date.strftime('%Y-%m-%d')}'"
        if end_date is not None:
            sql += f" and documents.timestamp <= '{end_date.strftime('%Y-%m-%d')}'"
        df = self.ds_conn.query(sql)
        return df
