# News Content package
This package contains a set of python classes to faciliate the searching and downloading of news articles.

The package uses the public GDELT API (https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/) to search for news articles by keywords (such as the name of a company) and then can filters these by language, source country, GDELT Theme and date ranges.

The API has has some limitations - I think there is a hardlimit of 250 articles per request.

The GDELT API does not return the content of the news article only the URL to the original source article which is downloaded seperately.

## Dependencies
The dependencies for this package are stored in the ```requirements.txt``` file in the package folder.

## Usage
The main class file is the ```ArticleExtractor``` class which currently has ```get_articles()``` method. This should be the main class used to download the articles.

This class orchestrates the querying of the GDELT database via the API and the downloading of the individual news articles into text. The following is an example usagage.
```
from news_content.article_extractor import ArticleExtractor

extractor = ArticleExtractor()
content = extractor.get_articles(keywords=["Software AG"],
                                 languages=['english'],
                                 source_countries=None,
                                 gdelt_themes=None,
                                 start_date="20230101",
                                 end_date="20231031",
                                 max_records=10)

for article in content:
    print(article[0:200])
```

### Filtering News Articles
The ```get_articles()``` method allows you to express some filters that are applied when the list of news articles is retrieved from GDELT. These are:

| Parameter        | Purpose                                                                                                                                                                                                                                                                          | Examples                       |
|------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------|
| keywords         | This is the list of terms we are searching for. If multiple terms are provided then these are OR'd together (GDELT does not support AND). This should be provided                                                                                                                | ["Software AG", "Bob's Farm]   |
| languages        | This is a list of languages that you want to restrict news articles to. The default is English but this can be overridden                                                                                                                                                        | ['french', 'german', 'arabic'] |
| source_countries | This is a list of the countries where you want news articles to come from. This is optional.                                                                                                                                                                                     | ['germany', 'france']          |
| gdelt_themes     | This is a list of Themes that GDELT has tagged the document with. A full list of GDELT themes is at http://data.gdeltproject.org/api/v2/guides/LOOKUP-GKGTHEMES.TXT  If multiple terms are provided then these are OR'd together (GDELT does not support AND). This is optional. | ["ENV_OIL", "ENV_MINING"]      |
| start_date       | This is the earliest date of the news articles you want to retrieve. This value should be provided and must be in either YYYYMMDDHHMMSS or YYYYMMDD format                                                                                                                       | 20231031                       |
| end_date         | This is the latest date of the news articles you want to retrieve. This value should be provided and must be in either YYYYMMDDHHMMSS or YYYYMMDD format                                                                                                                         | 20231031                       |
| max_records      | This is the number of records you want returned from GDELT and then subsequently downloaded. The default is 250 (the maximum supported by the GDELT API)                                                                                                                         | 10                             |.

## Article Downloader Script
This script combines the usage of the ```ArticleExtractor.get_articles()``` function with the list of target companies to produce a set of CSV files containing the downloaded news articles for the target companies.

The script is run from the command line using the command
```bash
python article_downloader --out_folder ./my_news
```

Currently, the script will read the target list of companies CSV file stored at ```../Organisation-Filtering/enriched/target_companies_list.csv```
This CSV file contains additional information about the target companies and so the script reads this into a dataframe to extract only the names of the companies to be targeted.

__Note__: This is currently hard-coded but could be parameter driven if there is a file that contains only the list of target company names or read from the Entity Datastore. This is later work that can be done

Using the list of company names, the script will query the GDELT new archive to obtain any relevant news articles and attempt to download the content for each article using the URL provided by GDELT.
The metadata about the news article and the content is then stored in a CSV format with 1 CSV per company. 
These CSV files can then be processed by the Data Enrichment Pipeline and stored in the Data Stores.

The script accepts the following command line arguments

| Argument Name | Description                                                                                                                                          |
|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| --out_folder  | This is the folder where the CSV files for each company is to be stored                                                                              |
| --start_date  | This is the earliest date for the news articles to be downloaded; if not provided yesterday's date is used.The data should be in __YYYYMMDD__ format |
| --end_date    | This is the latest date for the news articles to be downloaded; if not provided today's date is used. The data should be in __YYYYMMDD__ format.     |

__NOTE__: The GDELT News Database is free and open source but is Rate Limited to approximately 1 call every 5 seconds. 
Therefore, this script pauses between queries and so can take a while to run; this avoids triggering the Rate Limit which causes subsequent requests to fail.

