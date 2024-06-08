# Data Access Layer (DAL) Package
This package contains a set of class and function libraries used to access the datastores used by the User Interface.

## Usage
The DocumentStoreDAL is initialised using the constructor 
and calling one of its methods to return the sentiment timeline for an organization
```python
from documentstore import DocumentStoreDAL
from datetime import date


doc_store_dal = DocumentStoreDAL()
sent_df = doc_store_dal.get_sentiment_document_chunks(org_id = 1, start_date = date(2022, 10, 1), end_date = date(2023, 3, 30))

```

The following is a table of methods currently offered by the DocumentStoreDAL class

| Method                       | Description                                                                                                                                                                                                                         |
|------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| get_org_sentiment_timeline() | Returns the list of sentiment scores for documents that match the supplied Organization ID and within the specified start and end dates if provided. Returns the document id, document type, broad esg category and sentiment score |
| get_document() | Returns data about a single document|
|get_document_content() | Returns the stored content for the document|
|get_organisation_id_name()| Returns all the organisation id and names from the database|
|get_country()| Returns country name given org id|
|get_esg_data()| Returns ESG data given org id|
|get_green_washing_score()| Returns greenwashing score for the given org id|
|get_digital_identity_score()| Returns digital identity score for the given org id|
|get_ws_rank()| Returns ws_rank given ord id|
|get_licence_info()| Returns Certification(RSPO/RTRS) information given org_id
|get_sentiment_document_chunks()|Returns the list of sentiment scores for document parts that match the supplied Organization ID and within the specified start and end dates if provided. Returns the document id, document type, broad esg category and sentiment score|




