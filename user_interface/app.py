#VOY-Finance
#######################################################################################################
#Dependecies import
#######################################################################################################
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import plotly.express as px 
import time, datetime
from src.dal.documentstore import DocumentStoreDAL
from src.digital_identity import DigitalIdentity
from src import plots
from pathlib import Path
import streamlit_authenticator as stauth
# from dependancies import sign_up, fetch_users
######################################################################################################
#Page Config
######################################################################################################
st.set_page_config(
        page_title="VoY ESG Monitoring and Fraud Prevention in Trade Finance",
                       layout='wide', initial_sidebar_state="collapsed",page_icon="🌱")

######################################################################################################
#Authentication settings
# --- USER AUTHENTICATION ---


    
import yaml
from yaml.loader import SafeLoader

with open('.streamlit\\users.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)  
    
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
    ) 
    
    
    
name, authentication_status, username = authenticator.login('Login', 'main')
          

if authentication_status:
    authenticator.logout('Logout', 'main')

  
    
######################################################################################################

######################################################################################################
#Connection settings
######################################################################################################

    # Get organisation names
    doc_store_dal = DocumentStoreDAL()
    org_id_name = doc_store_dal.get_organisation_id_name()

    id_name = dict(zip(org_id_name['id'], org_id_name['name']))


    ######################################################################################################
    #Page Title
    ######################################################################################################
    st.title("🌎 ESG Monitoring and Fraud Prevention🌎")

    st.markdown("---")
    #######################################################################################################
    #Styling
    #######################################################################################################
    with open('style.css') as stlye:
        st.markdown(f'<style>{stlye.read()}</style>', unsafe_allow_html=True)



    ###################################################################
    #Body
    ###################################################################

    E_9 = ['Climate Change', 
            'Natural Capital', 
            'Pollution & Waste',        
            ]
    S_9 = ['Human Capital', 
            'Product Liability',
            'Community Relations',]
    G_9 = ['Corporate Governance', 
            'Business Ethics & Values']


    @st.cache_data  #  Add the caching decorator
    def load_sentiment_data(org_id, start_date, end_date):
        sent_df = doc_store_dal.get_sentiment_document_chunks(org_id, start_date, end_date)
        
        return sent_df


    col1, col2, col3 = st.columns(3)
    with col1:
        org_id = st.selectbox(
            'Choose a Company',
            options = list(id_name.keys()),
            format_func=lambda x: id_name[x],
            placeholder="Choose a Company")
    org_name = id_name[org_id]
    country = doc_store_dal.get_country(org_id)

    with col2:
        st.subheader(org_name)

    # Select esg data for the particular company
    esg_df = doc_store_dal.get_esg_data(org_id)

    # Check if there is no ESG data in the datastore
    if(esg_df.empty):
        st.markdown("No ESG score found in the database")
        esg_val = e_val = s_val = g_val = 0
        E_9_val = [0, 0, 0 ]
        S_9_val = [0, 0, 0] 
        G_9_val = [0, 0]

    else:
        esg_val = esg_df.ESG.values[0]
        e_val = esg_df.E.values[0]
        s_val = esg_df.S.values[0]
        g_val = esg_df.G.values[0]
        E_9_val = list(esg_df.E1_ClimateChange.values) + list(esg_df.E2_NaturalCapital.values) + list(esg_df.E3_PollutionWaste.values)
        S_9_val = list(esg_df.S1_HumanCapital.values) + list(esg_df.S2_ProductLiability.values) + list(esg_df.S3_CommunityRelations.values)
        G_9_val = list(esg_df.G1_CorporateGovernance.values)+ list(esg_df.G2_BusinessValueEthics.values)



    col_esg, col_gw_di= st.columns(2)


    dig_identity = DigitalIdentity()
    di_value, ws_rank = dig_identity.di_score(org_id)

    li_val_rspo, li_val_rtrs = dig_identity.get_licence_info(org_id)

    # show_table= False
    lei_no = dig_identity.get_LEI(org_name, False)

    sanction_status = dig_identity.get_sanction_status(org_name,country)
    # lei_no = DigitalIdentity.get_LEI(org_name, show_table = False)

    # 
    #  Green washing score from the datastore
    gw_df = doc_store_dal.get_green_washing_score(org_id)
    g_wash_score = gw_df.avg_gw.values[0]



    # Check if greenwashing score is null
    if g_wash_score is None:
        g_wash_score = 0

    with col_esg:    
        plots.plot_donut('ESG SCORE', esg_val, 'rgb(113,209,145)', 70, 450)
        
    with col_gw_di:
        col_gw, col_di = st.columns(2)
        with col_gw:
            g_wash_percentage = round(g_wash_score * 100, 2)
            st.markdown("""##### Greenwashing Probability """)
            st.metric(label="greenwash", value=f"{g_wash_percentage}%", label_visibility="hidden")
        
            st.markdown("<hr/>", unsafe_allow_html=True)

            st.markdown("""##### Certification Information """)
            st.write("RSPO certified:", li_val_rspo)
            st.write("RTRS certified:" , li_val_rtrs)
            st.markdown("<hr/>", unsafe_allow_html=True)


            st.markdown("""##### LEI and KYC Details """)
            st.write("LEI(Legal Entity Identifier): ", lei_no)

            st.write("Sanctions: ", sanction_status)

            # st.write("RTRS certified:" , li_val_2)

            # st.markdown('''
            #             #####
            #             ''')
                
        with col_di:
            st.markdown("""##### Digital Identity Score(DIS)""")
            st.metric(label="di", value=round(di_value,2), label_visibility="hidden")
            st.markdown(f'<p class="small-font"> DIS reflects how large a company\'s active social media following compared to an average fortune 1000 company </p>', unsafe_allow_html=True)
            
            
            st.markdown("""##### WS Rank""")
            st.metric(label="ws", value=round(ws_rank,2), label_visibility="hidden")
            st.markdown('<p class="small-font"> WS Rank indicates the quality of the company\'s offical website which includes latency, usability and keywords </p>', unsafe_allow_html=True)
        # st.markdown("<hr/>", unsafe_allow_html=True)
        
        
        
    st.markdown("---")

    col_E1, col_S1, col_G1 = st.columns(3) 
    with col_E1:
        plots.plot_donut('ENVIRONMENT', e_val, "#0DB7AC", 50, 200)
        plots.plot_bar(E_9, E_9_val, "#0DB7AC")

    with col_S1:
        plots.plot_donut('SOCIAL', s_val, "#0952AA", 50,200)
        plots.plot_bar(S_9, S_9_val, "#0952AA")

    with col_G1:
        plots.plot_donut('GOVERNANCE', g_val, "#F46544", 50,200)
        plots.plot_bar(G_9, G_9_val, "#F46544")
        
    st.markdown("---")
    col4, col5 = st.columns(2)

    if (org_id):
        # Set start and end date to fetch data
        with col4:
            start_date = st.date_input('Start date', datetime.datetime(2021, 1, 1)) 
        with col5:
            end_date = st.date_input('End date',datetime.datetime.now().date())
        

        df = load_sentiment_data(org_id, start_date, end_date)
        
        try:
            if df.empty:
                st.markdown("No relevant articles found in the database")
                raise ValueError("DataFrame is empty")
            
            # aggregate data based in timestamp and esg_category
            agg_df = df.groupby(['timestamp', 'esg_category'])['sentiment'].mean().reset_index()
            plots.plot_scatter(agg_df)

            with st.expander("Data preview"):
                st.dataframe(df)

        except ValueError as e:
            print("Exception caught:", e)
            

    st.markdown('<p style="font-size: 17px; text-align: center;">© 2024 Voy Finance. All rights reserved.</p>', unsafe_allow_html=True)

                
elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')

    try:
        if authenticator.register_user('Register user', preauthorization=True):
            st.success('User registered successfully')
            with open('.streamlit\\users.yaml', 'w') as file:
                yaml.dump(config, file, default_flow_style=False)   
    except Exception as e:
        st.error(e)
                