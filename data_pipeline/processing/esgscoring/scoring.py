
from PyPDF2 import PdfReader
import re
import pandas as pd
import numpy as np
from scipy import stats
import os

from ..corenlp.classification import EsgTextClassification

# ESG Scoring Function
#Analyze and score after scraping reports pdf to text

def scorer(We,Ws,Wg,path_to_reports):
  Epmean=[];Spmean=[];Gpmean=[]
  E1mean=[];E2mean=[];E3mean=[];S1mean=[];S2mean=[];S3mean=[];G1mean=[];G2mean=[]
  companies=E1=E2=E3=S1=S2=S3=G1=G2=E=S=G=ESG=[]
  directory_contents = os.listdir(path_to_reports)
  for file in directory_contents:
    #Dealing with EOF error in pdf's
    # opens the file for reading
    file_path = os.path.join(path_to_reports, file)
    with open(file_path, 'rb') as p:
        txt = (p.readlines())
    # Function to dealing with EOF error in pdf's
    def reset_eof_of_pdf_return_stream(pdf_stream_in:list):
        # find the line position of the EOF
        for i, x in enumerate(txt[::-1]):
            if b'%%EOF' in x:
                actual_line = len(pdf_stream_in)-i
                #print(f'EOF found at line position {-i} = actual {actual_line}, with value {x}')
                break

        # return the list up to that point
        return pdf_stream_in[:actual_line]
    # get the new list terminating correctly
    txtx = reset_eof_of_pdf_return_stream(txt)
    # write to new pdf
    with open(file_path, 'wb') as f:
        f.writelines(txtx)
    reader = PdfReader(file_path)

    number_of_pages = len(reader.pages)
    txt_all=[None]*number_of_pages
    for i in range(number_of_pages):
      page = reader.pages[i]
      txt_1 = page.extract_text()
      txt_all[i] = txt_1
    report=txt_all

    # Focus terms
    String1="Environmental"
    String2="Social"
    String3="Governance"

    # Extract text and do the search
    selec=[]
    for i in range(0, number_of_pages):
        PageObj = reader.pages[i]
        Text = PageObj.extract_text()
        if re.search(String1,Text) or re.search(String2,Text) or re.search(String3,Text):
            selected_pages=i
            selectp1=selec.append(selected_pages)
    #print(selec)
    #len(selec)
    # classify the text to ESG

    classifier = EsgTextClassification()
    number_of_pages=len(selec)
    broad_category=[None]*number_of_pages
    esg_topic=[None]*number_of_pages
    for i in range(number_of_pages):
      broad_category[i] = classifier.is_esg_related(report[selec[i]])

      esg_topic[i] = classifier.get_esg_topic(report[selec[i]])

    # Find the label with the maximum 'prob' value
    list1=[]
    list2=[]
    for i in range(number_of_pages):
      max_prob_dict = max(broad_category[i][0], key=lambda x: x['prob'])
      #print(max_prob_dict['label'],max_prob_dict['prob'])
      list1.append([max_prob_dict['label'],max_prob_dict['prob']])
      esg_topic_prob_dict = max(esg_topic[i][0], key=lambda x: x['prob'])
      #print(esg_topic_prob_dict['label'])
      list2.append([esg_topic_prob_dict['label'],esg_topic_prob_dict['prob']])

    # Broad-categories
    df1 = pd.DataFrame(list1)
    headers1 =  ["Broadcategory", "Prob"]
    df1.columns = headers1
    #print(df1)
    # Environmental
    xdf11=df1.loc[df1["Broadcategory"]=="Environmental"]
    #print(xdf11.describe())
    if len(xdf11)==0:
      maxEnvironmental=0.0
      meanEnvironmental=0.0
      #print('Emax=',maxEnvironmental,'Emean=',meanEnvironmental)
    else:
      maxEnvironmental=max(xdf11['Prob'])
      meanEnvironmental=xdf11['Prob'].mean()
      #print('Emax=',maxEnvironmental,'Emean=',meanEnvironmental)

    # Social
    xdf12=df1.loc[df1["Broadcategory"]=="Social"]
    #print(xdf12.describe())
    if len(xdf12)==0:
      maxSocial=0.0
      meanSocial=0.0
      #print('Smax=',maxSocial,'Smean=',meanSocial)
    else:
      maxSocial=max(xdf12['Prob'])
      meanSocial=xdf12['Prob'].mean()
      #print('Smax=',maxSocial,'Smean=',meanSocial)

    # Governance
    xdf13=df1.loc[df1["Broadcategory"]=="Governance"]
    #print(xdf13.describe())
    if len(xdf13)==0:
      maxGovernance=0.0
      meanGovernance=0.0
      #print('Gmax=',maxGovernance,'Gmean=',meanGovernance)
    else:
      maxGovernance=max(xdf13['Prob'])
      meanGovernance=xdf13['Prob'].mean()
      #print('Gmax=',maxGovernance,'Gmean=',meanGovernance)

    Epmean.append(meanEnvironmental)
    Spmean.append(meanSocial)
    Gpmean.append(meanGovernance)

    # esg-topics
    df2 = pd.DataFrame(list2)
    headers2=["ESGTOPICS","Prob"]
    df2.columns=headers2
    #print(df2)
    ## Environmental topics

    # Climate Change
    xdf21=df2.loc[df2["ESGTOPICS"]=="Climate Change"]
    #print(xdf21.describe())

    if len(xdf21)==0:
      maxClimatechange=0.0
      meanClimatechange=0.0
      #print('E1max=',maxClimatechange,'E1mean=',meanClimatechange)
    else:
      maxClimatechange=max(xdf21['Prob'])
      meanClimatechange=xdf21['Prob'].mean()
      #print('E1max=',maxClimatechange,'E1mean=',meanClimatechange)

    # Natural Capital
    xdf22=df2.loc[df2["ESGTOPICS"]=="Natural Capital"]
    #print(xdf22.describe())
    if len(xdf22)==0:
      maxNaturalcapital=0.0
      meanNaturalcapital=0.0
      #print('E2max=',maxNaturalcapital,'E2mean=',meanNaturalcapital)
    else:
      maxNaturalcapital=max(xdf22['Prob'])
      meanNaturalcapital=xdf22['Prob'].mean()
      #print('E2max=',maxNaturalcapital,'E2mean=',meanNaturalcapital)

    # Pollution & Waste
    xdf23=df2.loc[df2["ESGTOPICS"]=="Pollution & Waste"]
    #print(xdf23.describe())
    if len(xdf23)==0:
      maxPollutionwaste=0.0
      meanPollutionwaste=0.0
      #print('E3max=',maxPollutionwaste,'E3mean=',meanPollutionwaste)
    else:
      maxPollutionwaste=max(xdf23['Prob'])
      meanPollutionwaste=xdf23['Prob'].mean()
      #print('E3max=',maxPollutionwaste,'E3mean=',meanPollutionwaste)

    E1mean.append(meanClimatechange)
    E2mean.append(meanNaturalcapital)
    E3mean.append(meanPollutionwaste)

    ## Social topics

    # Human Capital
    xdf24=df2.loc[df2["ESGTOPICS"]=="Human Capital"]
    #print(xdf24.describe())
    if len(xdf24)==0:
      maxHumancapital=0.0
      meanHumancapital=0.0
      #print('S1max=',maxHumancapital,'S1mean=',meanHumancapital)
    else:
      maxHumancapital=max(xdf24['Prob'])
      meanHumancapital=xdf24['Prob'].mean()
      #print('S1max=',maxHumancapital,'S1mean=',meanHumancapital)

    # Product Liability
    xdf25=df2.loc[df2["ESGTOPICS"]=="Product Liability"]
    #print(xdf25.describe())
    if len(xdf25)==0:
      maxProductliability=0.0
      meanProductliability=0.0
      #print('S2max=',maxProductliability,'S2mean=',meanProductliability)
    else:
      maxProductliability=max(xdf25['Prob'])
      meanProductliability=xdf25['Prob'].mean()
      #print('S2max=',maxProductliability,'S2mean=',meanProductliability)

    # Community Relations
    xdf26=df2.loc[df2["ESGTOPICS"]=="Community Relations"]
    #print(xdf26.describe())

    if len(xdf26)==0:
      maxCommunityrelations=0.0
      meanCommunityrelations=0.0
      #print('S3max=',maxCommunityrelations,'S3mean=',meanCommunityrelations)
    else:
      maxCommunityrelations=max(xdf26['Prob'])
      meanCommunityrelations=xdf26['Prob'].mean()
      #print('S3max=',maxCommunityrelations,'S3mean=',meanCommunityrelations)

    S1mean.append(meanHumancapital)
    S2mean.append(meanProductliability)
    S3mean.append(meanCommunityrelations)

    ## Governance topics

    # Corporate Governance
    xdf27=df2.loc[df2["ESGTOPICS"]=="Corporate Governance"]
    #print(xdf27.describe())
    if len(xdf27)==0:
      maxCorporateGovernance=0.0
      meanCorporateGovernance=0.0
      #print('G1max=',maxCorporateGovernance,'G1mean=',meanCorporateGovernance)
    else:
      maxCorporateGovernance=max(xdf27['Prob'])
      meanCorporateGovernance=xdf27['Prob'].mean()
      #print('G1max=',maxCorporateGovernance,'G1mean=',meanCorporateGovernance)

    # Business Ethics & Values
    xdf28=df2.loc[df2["ESGTOPICS"]=="Business Ethics & Values"]
    #print(xdf28.describe())
    if len(xdf28)==0:
      maxBusinessethics=0.0
      meanBusinessethics=0.0
      #print('G2max=',maxBusinessethics,'G2mean=',meanBusinessethics)
    else:
      maxBusinessethics=max(xdf28['Prob'])
      meanBusinessethics=xdf28['Prob'].mean()
      #print('G2max=',maxBusinessethics,'G2mean=',meanBusinessethics)

    G1mean.append(meanCorporateGovernance)
    G2mean.append(meanBusinessethics)


  # Percentile scoring
  #Score-1
  Epmeanrank=[];Spmeanrank=[];Gpmeanrank=[]

  for i in range(len(Epmean)):
    Epmeanrank.append(stats.percentileofscore(Epmean, Epmean[i],kind='mean'))
    Spmeanrank.append(stats.percentileofscore(Spmean, Spmean[i],kind='mean'))
    Gpmeanrank.append(stats.percentileofscore(Gpmean, Gpmean[i],kind='mean'))

  ESGscore1=[]
  for i in range(len(Epmeanrank)):
    ESGscore1.append(We*Epmeanrank[i]+Ws*Spmeanrank[i]+Wg*Gpmeanrank[i])
  #print(ESGscore1)


  #Score-2

  Emeanrank=[];Smeanrank=[];Gmeanrank=[]
  Emean=list(1/3*(np.array(E1mean)+np.array(E2mean)+np.array(E3mean)))
  Smean=list(1/3*(np.array(S1mean)+np.array(S2mean)+np.array(S3mean)))
  Gmean=list(1/2*(np.array(G1mean)+np.array(G2mean)))

  for i in range(len(Emean)):
    #x=stats.percentileofscore(list, list[i],kind='strict')
    Emeanrank.append(stats.percentileofscore(Emean, Emean[i],kind='mean'))
    Smeanrank.append(stats.percentileofscore(Smean, Smean[i],kind='mean'))
    Gmeanrank.append(stats.percentileofscore(Gmean, Gmean[i],kind='mean'))

  ESGscore2=[]
  for i in range(len(Emeanrank)):
    ESGscore2.append(We*Emeanrank[i]+Ws*Smeanrank[i]+Wg*Gmeanrank[i])
  #print(ESGscore2)

  #Category subtopics scoring
  E1meanrank=[];E2meanrank=[];E3meanrank=[];S1meanrank=[];S2meanrank=[];S3meanrank=[];G1meanrank=[];G2meanrank=[]

  for i in range(len(E1mean)):
    #x=stats.percentileofscore(list, list[i],kind='strict')
    E1meanrank.append(stats.percentileofscore(E1mean, E1mean[i],kind='mean'))
    E2meanrank.append(stats.percentileofscore(E2mean, E2mean[i],kind='mean'))
    E3meanrank.append(stats.percentileofscore(E3mean, E3mean[i],kind='mean'))
    S1meanrank.append(stats.percentileofscore(S1mean, S1mean[i],kind='mean'))
    S2meanrank.append(stats.percentileofscore(S2mean, S2mean[i],kind='mean'))
    S3meanrank.append(stats.percentileofscore(S3mean, S3mean[i],kind='mean'))
    G1meanrank.append(stats.percentileofscore(G1mean, G1mean[i],kind='mean'))
    G2meanrank.append(stats.percentileofscore(G2mean, G2mean[i],kind='mean'))

  E1=E1meanrank;E2=E2meanrank;E3=E3meanrank;S1=S1meanrank;S2=S2meanrank;S3=S3meanrank;G1=G1meanrank;G2=G2meanrank

  for file in directory_contents:
    companies.append(file.replace('.pdf',''))

  #print(companies)

  #Assessing an avg and max approaches in ESG scoring
  ESGscore_avg=list(1/2*(np.array(ESGscore1)+np.array(ESGscore2)))
  ESGscoreall=np.array([ESGscore1,ESGscore2])
  ESGscore_max=ESGscoreall.max(axis=0)
  # for dashboard output
  E=list(np.array([Emeanrank,Epmeanrank]).max(axis=0))
  S=list(np.array([Smeanrank,Spmeanrank]).max(axis=0))
  G=list(np.array([Gmeanrank,Gpmeanrank]).max(axis=0))
  ESG=list(ESGscore_max)
  #print(ESGscore1)
  #print(ESGscore2)
  #print(ESGscoreall)
  #print(ESGscore_max)
  return companies,E1,E2,E3,S1,S2,S3,G1,G2,E,S,G,ESG