# Data Upload Scripts
This package contains a collection of scripts that are used to upload data into the Insights database

The following table lists the scripts available and further details of each script is provided in subsequent sections.

| Script Name        | Purpose                                                                 |
|--------------------|-------------------------------------------------------------------------|
| org_bulk_upload.py | Enables the bulk upload of new Organisations into the Insights database |


## Organisation Bulk Uploader
The `org_bulk_upload.py` script is used to upload new Organisations into the Insights database.
The script processes a CSV file containing the details of the new organisations and uploads them into the specified insights database.
The script will run in one of two modes:

**Insert Mode**
The script will process each row in the CSV file and check if the organisation matches an existing organisation. 
If it matches on name, then the record is rejected.
Otherwise, it is inserted as a new record.

**Update Mode**
The script will process each row in the CSV file and check if the organisation matches an existing organisation. 
If it matches on name, then any new data provided about the company in the CSV file is updated in the database. 
If there is no value specified in the CSV file, then the value is not updated.
If the organisation does not match an organisation in the database, it is rejected as not found.

> Note that currently, the ESG Platform cannot handle different organisations with the same name. 
> This is due to the lack of Named Entity Disambiguation in the current platform and would result in incorrectly assigning data to the wrong organisation. 

Where the script identifies records that are to be rejected, the script will generate a new CSV
file containing these rejected records so that these can be reviewed and re-processed if necessary.

When operating in **insert** mode, any rejected as duplicates are written to the `insert_rejects_<timestamp>.csv`
When operating in **update** mode, any rejected as not found are written to the `update_rejects_<timestamp>.csv`

These files only contain the rejected items can be be re-submitted if required by re-running this script using the appropriate mode

The script can be run from the command line as follows:
```bash
python org_bulk_upload.py --insight_db ./data/insights.db --data ./data/new_orgs.csv
```

The following table describes the command line arguments for this script

| Argument     | Mandatory | Description                                                                                                                                                                                                                                                       |
|--------------|-----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| --insight_db | Yes       | The full path to the insights database that you want the customers to be stored in                                                                                                                                                                                |
| --data       | Yes       | The full path to the CSV file containing the organisations to be uploaded                                                                                                                                                                                         |
| --mode       | No        | If set to `insert` the script will insert the organisations into the database unless they match an existing organisation. If set to 'update' the script will update the organisations in the database with the new details if it matches a record in the CSV file | 

The script processes a CSV file with the details for the organisations to be added. 
The script expects a standard CSV format with the following columns in any order - additional columns will be ignored:

| Column Name | Mandatory | Description                                                                                                                                       |
|-------------|-----------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| name        | Yes       | The name of the organisation - this will be the name presented in the UI and searched for when locating suitable documents                        |
| sector      | No        | The sector that the organisation belongs to e.g. Soy Producers                                                                                    |
| country     | No        | The country of operation for the organisation                                                                                                     |
| website     | No        | The organisation's website - while this is optional, some Digital Identity scores cannot be produced without a company website                    |
| linkedin    | No        | The organisation's page on LinkedIn - while this is optional, some Digital Identity scores cannot be produced without the company's LinkedIn page |
| profile     | No        | Description of the organisation                                                                                                                   |



