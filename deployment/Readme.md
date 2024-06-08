# Deployment
This document describes the Deployment of the Applicaiton and Data Pipeline.


# Deployment of a new Instance of the Application and Data Pipeline
The deployment of the Applicaiton and Data Pipeline involves the following steps
1. Deployment of required Azure Resources
2. Cloning the repository onto the Azure VM
3. Creating the Seed Insights database
4. Configuring the Streamlit Application
5. Running the Streamlit Application

These steps are described in the following sections

## Azure Resource Deployment
The current deployment configuration was chosen for simplicity of the deploymnet and ongoing maintenance. 
The deployment is not designed to be scalable or to optimise operating costs.

# Virtual Machine Deployment
The VM required for deployment should be:

| Property                   | Value                              |
|----------------------------|------------------------------------|
| Image                      | Ubuntu Server 20.04 LTS - x64 Gen2 |
| Size                       | Standard_D4 4 vcpus, 16 GiB memory |
| NIC network security group | Advanced                           |

> The remainder of the options can be set as required to create and deploy the VM
> 
> Note that the Size is selected so that the the Data Pipeline can be run
> The UI does not require a VM of this size and could be run using a Standard D2 image



# Adding Network Rule
To be able to access the ESG Scoring and Insights application, the VM needs to expose Port 80.

In the azure portal, select the _Network Security Group_ associated with the VM and add a new _Inbound security rule_ with the following properties:

| Field                   | Value |
|-------------------------|-------|
| Destination port ranges | 80    |
| Protocol                | TCP   |

> The remainder of the fields can be left as the default values or custom values provided


## Cloning the application
To run the application and data pipeline, we need to clone the project repository. 
This following instructions should be performed from your Azure SSH session to the VM.

```bash
mkdir repos
cd repos
git clone https://dagshub.com/Omdena/Voy-Finance.git
```
pyt
This will download the whole project repository to a `repos` folder.

### Install Python Dependencies 
The various Python Dependencies are stored in `Voy-Finance/results/final-code/requirements.txt`
These can be installed using the following command.

> The version of Python installed in the base image is 3.8 and the applicaiton required version 3.10
> Upgrading the version of Python in the base image does appear to work so, there is a need to upgrade the base Unbutu image
> before installing the Python Dependencies (we could also use anaconda but that requires various setup to run from a script)

Check the version of Python installed using
```bash
python3 --version
````
If the version is less than 3.10 then run the following commands to upgrade the base image

```bash
sudo apt-get update && sudo apt-get upgrade
sudo do-release-upgrade
```

> The VM may need to restart and so after the restart you can reconnect and check the version of Python with
```bash
python3 --version
````
The version should be greater than 3.10

With the Python requirement met we can install the application dependencies using 
```bash
sudo -H pip install -r /home/azureuser/repos/Voy-Finance/src/results/final-code/requirements.txt
```
 
> If pip is not currently installed, it can be installed using `sudo apt-get install python3-pip`

The required dependencies should now be installed

By default 


## Copy application code
The repository contains all the code that was created during the project and not all is required to run the MVP platform.
The following steps allow you to copy the required code into the application folders. 
This also means any configuration we set is not overwritten of need to pull the updated code from DagsHub 


```bash
cd ~
mkdir esgscoring
cd esgscoring
mkdir app
mkdir data
mkdir data_pipeline
mkdir data_upload
```

We can now copy the required files into the application folders.

```bash
cp -r ~/repos/Voy-Finance/src/results/final-code/user_interface/. ./app
sudo chown -R azureuser:azureuser /home/azureuser/esgscoring/app/.streamlit

cp -r ~/repos/Voy-Finance/src/results/final-code/data_pipeline/. ./data_pipeline
cp -r ~/repos/Voy-Finance/src/results/final-code/data_upload/. ./data_upload
```

## Obtaining the seed database
The seed insights database can be downloaded from the Omdena Google Drive.

Then we can download the seed insights database into the data folder with the following command
```bash
wget "https://drive.google.com/uc?export=download&confirm=yes&id=1ptV2F4c2RSndymf4xh-EwTURyd1m4IKe" -O ~/esgscoring/data/insights.db

```
> Note that the `id` of the file provided in the url may change if a newer version of the seed database is uploaded or is moved.

If the seed insights database is not available it can be created by running the scripts in the `deployment/data-stores` folder.
These scripts are numbered and should be run in order; please refer to the README.md file in the `deployment' folder.
This will create an empty insights database which needs to be populated. 

## Application Configuration
For the Streamlit Application we need to configure the following items:
1. The path to the insights database
2. The path tp the Users file
2. The API Key for the KYC-Chain API
3. The pre-approved users list

The path to the database, users file and the API keys are held in the `.streamlit/secrets.toml` file. 
The following commands create this file and populates it with the correct details:

The easiest method to update the **secrets.toml** file is to use the nano editor.

```bash
cd ~/esgscoring/app/.streamlit
nano secrets.toml
```

With the Nano editor open, you need to provide your KYC-Chain API key for the **API_KEY** entry. 
The Key should be between the double quotes.

You then need to set the value of the **connections.document_store** URL as follows:
```text
url = "sqlite:////home/azureuser/esgscoring/data/insights.db"
```
You also need to set the value of the **users_file_path** as follows:
```text
"users_file_path" = "/home/azureuser/esgscoring/app/.streamlit/users.yaml"
```
When these updates are complete, press Ctl+S then Ctl+X to save the changes and then exit.

The list of pre-authorised users can be found in the **users.yaml** file. 
By default, the email address **projects@omdena.com** is pre-authorised and so can be used to register an account.
However, you can add additional accounts by adding email addresses to the list of emails in this file.

The easiest method to edit the **users.yaml** file is using Nano.

```bash
cd ~/esgscoring/app/.streamlit
nano users.yaml
```

> Note that this is a Yaml file and so the format must be preserved.
> New users must be defined on a new line, with 2 spaces followed by a hyphen and a space then the email address.

## Running the UI Application
The streamlit application can be run using the **run.sh** file but must be made an executable first.
```bash
cd ~/esgscoring/app/
chmod +x run.sh
```

The script can be run using the following command
```bash
cd ~/esgscoring/app/
sudo ./run.sh
```
This will start the Streamlit application from the commandline - this should be used to check that the application is running 
but is not suitable for running the application long term since the application will stop when the SSH session ends.

To ensure the Streamlit app is run each time the VM is started, we add the script to the CRONTAB using the command
```bash
sudo crontab -e
```

We then add the following to the end of the crontab
```text
@reboot /home/azureuser/esgscoring/app/run.sh
```

The VM should then be restarted and this will cause the Streamlit app to be started as a background task

## Data Stores
This section discusses the scripts required to recreate the _insights_ database if the seed database is not available.

The `data-stores` package contains the set of scripts that are used to create and initialise these with the relevant schemas.

The following table lists the data store initialisation scripts and further information is provided in subsequent sections.

| Initialisation Script                   | Description                                                                                                                     |
|-----------------------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| 1_initialise_organisations_datastore.py | Script to initialise the tables within the Insights database that hold the data about the target companies                      |
| 2_initialise_document_datastore.py      | Script to initialise the tables within the Insights database that hold the documents about companies and the extracted insights |
| 3_initialise_esg_scores_datastore.py    | Script to initialise the tables within the Insights database that hold the ESG scoring for organisations                        |
| 4_initialise_di_scores_datastore.py     | Script to initialise the tables within the Insights database that hold the Digital Identity scoring for organisations           |
 
### Initialising the Organisations Data Store
The Organisations Data Store is a set of tables within the `insights` (SQLite3) database that holds information about the target companies. 
This includes the given name of the company, their main website address, country of operation, links to certifications they hold.

The `1_initialise_organisations_datastore.py` script is required when setting up a new Insights database and can be run as from the command line as follows:
```bash
python 1_initialise_organisations_datastore.py --path ./data --delete_existing True --load_data ./org_data/orgs_list.csv
```

The script takes the following command line arguments

| Argument          | Description                                                                                                                                                                                                            |
|-------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| --path            | Path to folder where you want the Organisation Datastore to be created. The script looks for an `insights.db` file in this location and attempts to use it. If it does not exist, the script creates the database file |
| --delete_existing | Set to True if you want to delete any existing Organisation tables and data from the datastore. Default is False                                                                                                       |
| --load_data       | Set to path to the folder where the Organization data is if you want to load the datastore; otherwise omit to begin with an empty datastore. See below for format of the Organisation data                             |

When using the `--load_data` argument, the script expects the full path to a CSV file containing the list of organisations to be created. This CSV file must have the following columns:

| Column name    | Content Description                                                        |
|----------------|----------------------------------------------------------------------------|
| name           | The name of the organisation                                               |
| country        | the country that the organisation operates in                              |
| sector         | the sector that the organisation operates in (e.g. palm oil - distributor) |
| certifier_site | the site URL of the Certifier that the company details was extracted from  |
| member_id      | the member id of the organisation for the certifier                        |
| website        | the website of the organisation                                            |
| profile        | text that describes the organisation                                       |

> **Note**: The above format is based on the seed data that was extracted from the RSPO Membership pages.
> This option is not intended as a general purpose mechanism to load new organizations into the database.
> 
> A copy of the seed data in this format can be found in the `seed-data` folder.


## Initialising the Document Data Store
The Document Data Store is a set of tables in the `insights.db` that holds documents and text insights for those documents.
Currently, this data store is used to hold News Articles about target organisations and the insights derived from those such as the ESG Category, Sentiment, Keywords Entities, etc.

The `2_initialise_document_datastore.py` script is required when setting up a new Insights database and can be run as from the command line as follows:
```bash
python 2_initialise_document_datastore.py --path ./data --delete_existing True --seed_data_path ./news-downloads
```

The script takes the following command line arguments

| Argument          | Description                                                                                                                                                                                                            |
|-------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| --path            | Path to folder where you want the Organisation Datastore to be created. The script looks for an `insights.db` file in this location and attempts to use it. If it does not exist, the script creates the database file |
| --delete_existing | Set to True if you want to delete any existing Document tables and data from the datastore. Default is False                                                                                                           |

> **Note:** To load seed data into the Document Datastore, you should use the following scripts:
> `data-pipeline/processing/news_text_insights.py`
> `data-pipeline/processing/gw_detection_sustainability_reports.py`

## Initialising the Digital Identify Data Store
The Digital Identity Data Store is a set of tables in the `insights` that holds Digital Identify Scoring information for Organisations.

The `3_initialise_di_scores_datastore.py` script is required when setting up a new Insights database and can be run as from the command line as follows:
```bash
python 3_initialise_di_scores_datastore.py --path ./data --delete_existing True --load_data ./di-scores
```

The script takes the following command line arguments

| Argument          | Description                                                                                                                                                                                                            |
|-------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| --path            | Path to folder where you want the Organisation Datastore to be created. The script looks for an `insights.db` file in this location and attempts to use it. If it does not exist, the script creates the database file |
| --delete_existing | Set to True if you want to delete any existing Document tables and data from the datastore. Default is False                                                                                                           |
| --migrate_data    | This is used to migrate data stored in the Digital Identity CSV files (as produced by the DI Scoring Team) into the format used within the **insights** database                                                       |

## Initialising the ESG Scoring Data Store
The ESG Scoring Data Store is a set of tables in the `insights.db` that holds ESG Scoring information for Organisations.

The `initialise_document_datastore.py` script is required when setting up a new Insights database and can be run as from the command line as follows:
```bash
python 4_initialise_esg_scores_datastore.py --path ./data --delete_existing True --load_data ./esg-scores/ESGdatabase.db
```

The script takes the following command line arguments

| Argument          | Description                                                                                                                                                                                                            |
|-------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| --path            | Path to folder where you want the Organisation Datastore to be created. The script looks for an `insights.db` file in this location and attempts to use it. If it does not exist, the script creates the database file |
| --delete_existing | Set to True if you want to delete any existing Document tables and data from the datastore. Default is False                                                                                                           |
| --load_data       | This is used to migrate data stored in an existing ESGDatabase file (as produced by the ESG Scoring Team) into the format used within the **insights** database                                                        |



