from python_lei.lei_search import SearchLEI

import streamlit as st
from src.dal.documentstore import DocumentStoreDAL
from src.sanctions_check import KycChainApiClient
KYC_API_TOKEN = st.secrets["API_KEY"]
import json
import pycountry
import numpy as np

class DigitalIdentity:
    """
    Class that encapsulates the application logic required for retrieving information related to Digital identity.
    The information includes 
        - Digital Identity Score
        - ws rank
        - RSPO cerfication/RTRS certification
        - Legal Entity Identification

    """
    
    def __init__(self):
        """
        Constructor for the DigitalIdentity class
        """
        self.doc_store_dal = DocumentStoreDAL()
        self.search_possible_lei = SearchLEI()
        self.kyc = KycChainApiClient(KYC_API_TOKEN)

    def di_score(self,org_id):
        """
        This module retrieves the digital identity score and ws score from the datastore
        """
        di_df = self.doc_store_dal.get_digital_identity_score(org_id)

        if di_df.empty:
            di_value = 0
        else:
            di_value = di_df.score.values[0]

        # Get rank from the datastore
        ws_df = self.doc_store_dal.get_ws_rank(org_id)

        if ws_df.empty:
            ws_rank = 0
        # ws_rank = round(ws_df.score.values[0], 2)
        else:
            ws_rank = ws_df.score.values[0]
        return di_value, ws_rank
        
    def get_licence_info(self, org_id):
        """
        This module retrieves licence information from datastore
        """
        licence_df = self.doc_store_dal.get_licence_info(org_id)
        licence_dict = dict(zip(licence_df.certifier, licence_df.licence_state))
        if licence_df.empty:
            li_val_rspo = li_val_rtrs = 'N/A'
        else:
            if (licence_dict['rspo'] == 1):
                li_val_rspo = "yes"
            else:
                li_val_rspo = "No"

            if (licence_dict['rtrs'] == 1):
                li_val_rtrs = "yes"
            else:
                li_val_rtrs = "No"
        return li_val_rspo, li_val_rtrs

    def get_LEI(self,org_name, show_table = False):  
        """
        This module uses Python wraper for Legal Entity Identification API to search LEI for the organisations
        
        """
        self.search_possible_lei = SearchLEI() 
        
        try:            
            
            raw_data = self.search_possible_lei.search_lei(org_name, show_table)
            
            if(raw_data is None):
                return 'Not available'
            else:
                return raw_data[0]['LEI']
            

        except Exception as e:
            # Log the error
            print(f"Error: {e}")   

    def get_sanction_status(self,org_name,country):
        # pycountry library uses the list of country names from https://en.wikipedia.org/wiki/ISO_3166-1
        # If the country name in our database is old, we need to update the name in db
        # In this case, 'Czechia' is used by pycountry but our database has the name 'Czech Republic' 
        # manually assigned the name 'Czechia' 

        if(country.values[0][0] == 'Czech Republic'):
            country.values[0][0] = 'Czechia'
        
        if(country.values[0][0] is not None):            
        
            if(pycountry.countries.get(name=country.values[0][0]) is None):
                return "Can't access API/country code doesnot match"
            else:
                
                country_code = pycountry.countries.get(name=country.values[0][0]).alpha_2
            
                country_code_list  = [country_code] + ["US", "GB", "EU" ]
                
                try:  
                    sanctions = self.kyc.get_sanctions_by_company_name(org_name, country_code_list, 0.8)
                    if len(sanctions) > 0:
                        return 'Yes'
                    else:
                        return 'No'                   
                except Exception as e:
                    # Log the error
                    print(f"Error: {e}")  
                 
        else:
            return "Country details not available"        
        