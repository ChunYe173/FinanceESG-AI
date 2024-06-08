# Data Pipeline
These folders contain the code necessary to download and process data to generate the insights required by the User Interface and for analytics.

There are two packages:
1. **extraction** - this contains the scripts necessary to download new data that is used in the application. 
2. **processing** - this contains the scripts necessary to process the downloaded data to generate the analytics and insights an then store the results in the datastores.

The following sections describe these packages in more detail and provide the usage instructions

## Extraction scripts
The _extraction_ folder contains the scripts and supporting libraries required to download new data that is used to generate analytics and insights.

Running the code make calls to external APIs and data sources to obtain the relevant data used in the processing. Each script is designed to be run as from the command line and accepts a set of arguments to parameterize the execution of the script.

In a production setting, these scripts would be run on a schedule to extract newer data about the customers. 

The following table describes the main extraction scripts 

| Extraction Script               | Purpose                                                                                                                                                                                                              |
|---------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| news-article-downloader.py      | Obtains a list of customer names and alias terms and makes calls to the GDELT News Archieve to find new news articles about the companies and then attempts to extract the text of the news articles from the source |
| di_linkedin_stats_downloader.py | Obtains statistics from a company's LinkedIn page, if the company has a LinkedIn paged defined in the insights database. This is used to compute the _digital score_ for the company                                 |
| di_seo_stats_downloader.py      | Obtains statistics from the company's website if we have a website defined for the company in the  in the insights database.  This is used to compute the _ws rank_ for the company                                  |                                                                                                              |

### News Article Downloader
The `news-article-downloader.py` script attempts to locate news articles from the GDELT News Archive (https://www.gdeltproject.org/) for each of the target companies.
The script performs a date range bound search with the company name as a keyword to obtain the list of news articles.
Where a search yields one or more articles, the script then attempts to download the content of that news article from the news source.
The resulting articles for the company are stored in CSV file format that contains the news article metadata and the news content if it was downloaded.
The set of CSV files that are created are then available for downstream processing to extract insights and analytics.

> Note: Not all news articles can be downloaded, the GDELT database provides a link to the source news article, but we may not be able to download this for a number of reasons such as:
> 1. the article has been removed
> 2. the article requires the client to register/sign in
> 3. the article is behind a paywall.
> 
> The current script is unable to cater for these across the wide range of news sources and so this yields empty news content. 
> As further work, this could be extended to deal with these scenarios.

The script run from the command line using the command
```bash
python news_article_downloader.py --insights_db_path ./data-stores/insights.db --out_folder ./my_news
```

The script accepts the following command line arguments

| Argument Name      | Description                                                                                                                                          |
|--------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| --insights_db_path | This is the path to the insights database (sqlite3 file)                                                                                             |
| --out_folder       | This is the folder where the CSV files for each company is to be stored                                                                              |
| --start_date       | This is the earliest date for the news articles to be downloaded; if not provided yesterday's date is used.The data should be in __YYYYMMDD__ format |
| --end_date         | This is the latest date for the news articles to be downloaded; if not provided today's date is used. The data should be in __YYYYMMDD__ format.     |

> __NOTE__: 
> The GDELT News Database is free and open source but is Rate Limited to approximately 1 call every 5 seconds. 
> Therefore, this script pauses between queries and so can take a while to run; this avoids triggering the Rate Limit which causes subsequent requests to fail.


### LinkedIn Statistics Downloader
The `di_linkedin_stats_downloader.py` script attempts download follower statistics from LinkedIn for companies in the insights database where we have a valid LinkedIn page for them
The script uses Selenium Webdriver to scrap the data from LinkedIn and produces a JSON file that stores the following information for each organisation (that has a LinkedIn page)
* org_id : this is the unique ID of the organisation within the insights database.
* followers: this is the number of followers of the company's page as stated by LinkedIn
The JSON file is stored for downstream processing and the generation of the digital score

The script is run from the command line using the command
```bash
python di_linkedin_stats_downloader.py --insights_db_path ./data-stores/insights.db --out_folder ./my_news
```

The script accepts the following command line arguments

| Argument Name | Description                                                                   |
|---------------|-------------------------------------------------------------------------------|
| --insights_db | This is the path to the insights database (sqlite3 file)                      |
| --out_folder  | This is the folder where the JSON file for the downloaded data will be stored |

### Website Statistics Downloader
The `di_seo_stats_downloader.py` script attempts download website metrics from the target organisation's website.
The script uses a SEO Analyzer  to extract metrics from about the website and stores these in a JSON file for downstream processing and the generation of the ws rank

The script is run from the command line using the command
```bash
python di_seo_stats_downloader.py --insights_db_path ./data-stores/insights.db --out_folder ./my_news
```

The script accepts the following command line arguments

| Argument Name | Description                                                        |
|---------------|--------------------------------------------------------------------|
| --insights_db | This is the path to the insights database (sqlite3 file)           |
| --out_folder  | This is the folder where the JSON file for the data will be stored |

## Processing Scripts
The _processing_ folder contains the scripts and supporting libraries required to process downloaded data to generate analystics and insights; these are then stored the relevant datastores for downstream usage.

The following table describes the processing scripts

| Script                    | Description                                                                                                                                                                                         |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| news_text_insights.py     | Script processes news articles downloaded using the `news_article_downloader.py` script and generates insights from the news article content and stores these in the insights database              |
| esg_scoring.py            | Script that processes a set of Sustainability Reports (pdfs) and produces ESG scores for customers.                                                                                                 |
| generate_digital_score.py | Script to process previously downloaded LinkedIn Follower data and previously stored ws_rank data to produce a digital score for a company. The computed scores are stored in the insights database |                                             
| generate_ws_ranks.py      | Script to process previously downloaded Website statistics data to generate a ws_rank for the company. The computed scores are stored in the insights database                                      |                                             


### Extract Text Insights From News Articles
The `news_text_insights.py` script processes the news articles that were downloaded using the `news_article_downloader.py` script and generates the various text based insights.
These insights are stored in the `insights.db` within the Document tables.

The script is designed to be run from the command line as follows:
```bash
python news_text_insights.py --data_folder ./news-articles --source gdelt --insight_db ./insights.db
```

The following table lists the command line arguments for this script

| Argument      | Description                                                                                                                                               |
|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| --data_folder | This is the path to the folder that contains the output from the `news_article_downloader.py` script to be processed                                      |
| --source      | This is a flag to indicate the source of the news articles. Currently only support 'gdelt' and this parameter defaults to this value so can be excldued |
| --insight_db  | The full path to the (sqlite3) insights database file where you want the extracted insights to be stored                                                  |


### Producing Organisation ESG Scores from Sustainability Report PDFs
The `esg_scoring.py` script is used to generate ESG scores for Organisations based on their Sustainability Report (pdf).
Once scored, these ESG Scores are stored in the _insights_ database with a timestamp indicating when the score was generated.

The script is designed to be run from the command line as follows:
```bash
python esg_scoring.py --data_folder ./sustain-reports --insight_db ./insights.db
```

The following table lists the command line arguments for this script

| Argument      | Description                                                                                                    |
|---------------|----------------------------------------------------------------------------------------------------------------|
| --data_folder | Path to folder where the Sustainability Report files to be processed are stored                                |
| --insight_db  | The full path to the (sqlite3) insights database file where you want the extracted ESG Scores are to be stored |
| --weight_e    | The weighting to apply to Environment scores in the overall ESG score. Default 0.45                            |
| --weight_s    | The weighting to apply to Social scores in the overall ESG score. Default 0.30                                 |
| --weight_g    | The weighting to apply to Governance scores in the overall ESG score. Default 0.25                             |
 
> **Note** The Sustainability Reports stored in the data folder must have the name of the Organisation as the file name. 
> Without this, the script will not be able to link the ESG scores to the correct organisation within the **insights** database


### Generate WS RANK for companies
The `generate_ws_ranks.py` script processes the previously downloaded website statistics (generated using the `di_seo_stats_downloader.py` script) and generates the ws_score for the company.
These scores are stored in the `insights.db` within the _organisations_di_scores_ tables.

The script is designed to be run from the command line as follows:
```bash
python generate_ws_ranks.py --data_folder ./seo_data --insight_db ./insights.db
```

The following table lists the command line arguments for this script

| Argument      | Description                                                                                                                                                                                  |
|---------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| --data_folder | This is the path to the folder that contains the output from the `di_seo_stats_downloader.py` script to be processed.  |
| --insight_db  | The full path to the (sqlite3) insights database file where you want the extracted insights to be stored                                                                                     |

> Note: The script will process all files within the data folder that meets the naming convention
> These file use the naming convention __seo_stats_YYYYMMDDHHMMSS.json__


### Generate DIGITAL SCORE  for companies
The `generate_digital_scores.py` script processes the previously downloaded LinkedIn Follower statistics (generated using the `di_linkedin_stats_downloader.py` script) and generates the ws_score for the company.
These scores are stored in the `insights.db` within the _organisations_di_scores_ tables.

The script is designed to be run from the command line as follows:
```bash
python generate_digital_scores.py --data_folder ./seo_data --insight_db ./insights.db
```

The following table lists the command line arguments for this script

| Argument      | Description                                                                                                                                                                                       |
|---------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| --data_folder | This is the path to the folder that contains the output from the `di_linkedin_stats_downloader.py` script to be processed. These file use the naming convention __seo_stats_YYYYMMDDHHMMSS.json__ |
| --insight_db  | The full path to the (sqlite3) insights database file where you want the extracted insights to be stored                                                                                          |

> Note: The script will process all files within the data folder that meets the naming convention
> These file use the naming convention __linkedin_stats_YYYYMMDDHHMMSS.json__



## Data Stores
The Data Pipeline interacts with a set of Data Stores that hold different types of data about the companies. 
The majority of the analytics and insights are stored in a relational database known as the _insights_ database. 
However, other more specialised data stores are also used for some extracted data. The following table describes these.

| Data Store | Type       | Purpose                                                 |
|------------|------------|---------------------------------------------------------|
| insights   | Relational | the main data store for analytics, scoring and insights |

