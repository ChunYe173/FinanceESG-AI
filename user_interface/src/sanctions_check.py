import json
from cleanco import basename
import streamlit as st
from Levenshtein import distance

import requests

KYC_API_TOKEN = st.secrets["API_KEY"]

# Helper functions to process the CheckData response


def _compute_name_similarity(
    s1: str, s2: str, case_insensitive: bool = True, remove_org_type: bool = True
) -> float:
    """Computes the similarity between two company names as a percentage with 1.0 being a perfect match and 0.0 being a no match.

    The similarity is computed using the Levenshtein distance (a common text similarity metric) and is generally
    performed using a case-insensitive comparison. By default, we also remove any organisation type indicators such as
    Limited, Ltd, Inc. etc.  These can have different forms and so make computing a similarity more difficult.

    :param s1: First string
    :param s2: Second string
    :param case_insensitive: Set to True (default) to perform a case-insensitive comparison, or False to perform
        case-sensitive comparison
    :param remove_org_type: Set to True (default) to remove any organisation type indicators before computing the
        similarity, or False to leave these indicators untouched

    Returns a similarity value in the range 0.0 to 1.0 with values close to 1.0 being a good match
        and values close to 0.0 being a poor match
    """
    # Normalise the strings (we could remove some punctuation chars such as commas, double quites etc. as well)
    s1 = s1.strip().replace("  ", " ")
    s2 = s2.strip().replace("  ", " ")

    if case_insensitive:
        s1 = s1.lower()
        s2 = s2.lower()
    if remove_org_type:
        s1 = basename(s1).strip()
        s2 = basename(s2).strip()
    name_dist = distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return 1.0 - (name_dist / float(max_len))


def _get_closest_company_match(company_name: str, kyc_data: dict) -> (str, int, dict):
    """
    Processes the kyc Data-Checks response JSON to find the entry where the company name matches
        closest to the query term.

    :param company_name: The company name that was queried for
    :param kyc_data: The json returned from the KYC-Chain DataChecks API endpoint.
    :return: A tuple containing the best matched company name, the similarity score and the data related to this company
    """
    target_entry = {}
    target_company_name = None
    company_name = company_name.lower()
    max_score = 0.0
    for item in kyc_data["complyAdvantageEntities"]:
        name = item["key_information"]["name"].lower()
        # compute similarity
        sim_score = _compute_name_similarity(company_name, name)
        if sim_score == 1.0:
            # exact match found to terminate early
            max_score = sim_score
            target_entry = item
            target_company_name = name
            break
        elif sim_score > max_score:
            max_score = sim_score
            target_entry = item
            target_company_name = name
    return target_company_name, max_score, target_entry


def _extract_sanctions_for_customer_entry(
    target_entry: dict,
) -> list[(str, list[str], str, str)]:
    # def _extract_sanctions_for_customer_entry(
    #     target_entry: dict,
    # ):
    """
    Extracts any sanctions for a customer entry that was returned by the KYC-Chain DataChecks api.
    This is achieved by processing the list of warnings for the organisation and looking for warnings where there is
    an "offence" listed. Warnings that do not have an offence listed are ignored.

    :param target_entry: The data from KYC-Chain DataChecks for a specific company
    :return: A list of tuples containing the name of the organisation issuing the sanction, the country of issue,
        the location of the sanction and the details of the sanction.
    """
    sanctions = []
    if (
        "full_listing" in target_entry.keys()
        and "warning" in target_entry["full_listing"].keys()
    ):
        for entry in target_entry["full_listing"]["warning"].items():
            if entry[1]["listing_ended_utc"] is not None:
                # Sanction is not active
                continue
            warning_org = entry[1]["name"]
            country_code = entry[1]["country_codes"]

            location_url = None
            is_offence = False
            sanction_details = ""
            for warning in entry[1]["data"]:
                if warning["name"] == "Locationurl":
                    location_url = warning["value"]
                if warning["name"] == "offence":
                    is_offence = True
                    sanction_details = warning["value"]
            if is_offence:
                sanctions.append(
                    (warning_org, country_code, location_url, sanction_details)
                )
    return sanctions


class KycChainApiClient:
    """
    API Client for the Voy Finance Instance of the KYC-Chain API
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        # self.base_url = "https://voyfinance.instance.kyc-chain.com/api"
        self.base_url = (
            "https://voyfinance.instance.kyc-chain.com/integrations/v3/scope/voyfinance"
        )

    def get_sanctions_by_company_name(
        self, company_name: str, countries: list[str], min_name_similarity: float = 0.80
    ) -> list[str]:
        """
        Retrieves the list of sanctions for a company by company name from the KYC-Chain DataChecks API.
        The search by company name can result in multiple matches and false positives so a similarity check is performed
        on the returned matches to ensure we find a close match. Only the sanctions for the closest match is returned.
        If there are no matches found or there are no good quality matches, then an empty list is returned

        :param company_name: The name of the company to find sanctions for
        :param countries: The list of countries to search for sanctions. Code must use the ISO 3166-1 alpha-2 format
        :param min_name_similarity: The minimum company name similarity to consider a match. The default is 0.80

        :return: A list of tuples containing the name of the organisation issuing the sanction, the country of issue,
        the location of the sanction and the details of the sanction.
        """
        if company_name is None or len(company_name) == 0:
            raise ValueError("The company name must be provided")

        if countries is None or len(countries) < 2:
            raise ValueError("You must provide at least 2 countries")

        sanctions = []
        # Create Request
        params = [f"countryCodes={country}" for country in countries]
        params.append(f"name={company_name}")
        query_string = "&".join(params)
        endpoint = f"{self.base_url}/data-checks/entity?{query_string}"

        # Get Response
        response = requests.get(
            endpoint, headers={"Accept": "application/json", "apikey": self.api_key}
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to retrieve sanctions. Status code: {response.status_code}. Response text: {response.text}"
            )

        # Filter Response to best match within the results
        target_name, similarity, target_entry = _get_closest_company_match(
            company_name, response.json()
        )
        if target_name is not None and similarity >= min_name_similarity:
            # Extract the sanctions for this entry
            sanctions = _extract_sanctions_for_customer_entry(target_entry)
        # res = json.dumps(response.json(), indent=4, sort_keys=True)
        # print(res)
        return sanctions

    def get_sanctions_by_registration_id(
        self, registration_id: str, country_code: str
    ) -> list[str]:
        """
        Retrieves the list of sanctions for a company by company registration id
        NOTE: This seems to result in a HTTP 500 (Internal Server Error) when called - probably a problem with the KYC-Chain API

        :param registration_id: The name of the company to find sanctions for
        :param country_code: The Country code to search for the sanctions

        :return: A list of tuples containing the name of the organisation issuing the sanction, the country of issue,
        the location of the sanction and the details of the sanction.
        """
        if registration_id is None or len(registration_id) == 0:
            raise ValueError("The company registration id must be provided")

        if country_code is None:
            raise ValueError("You must provide a country code")

        sanctions = []
        # Create Request
        # The spelling mistake in the "country" parameter is from the swagger docs
        query_string = f"coutry={country_code}&registrationNumber={registration_id}"
        endpoint = f"{self.base_url}/data-checks/registration_number?{query_string}"

        # Get Response
        response = requests.get(
            endpoint, headers={"Accept": "application/json", "apikey": self.api_key}
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to retrieve sanctions. Status code: {response.status_code}. Response text: {response.text}"
            )

        # Extract the sanctions for this entry
        sanctions = _extract_sanctions_for_customer_entry(response.json())
        return sanctions


# def main():
#     kyc = KycChainApiClient(KYC_API_TOKEN)
#     company_name = "Cargill Soluciones Empresariales"
#     sanctions = kyc.get_sanctions_by_company_name(company_name, ["US", "GB"], 0.8)
#     print("Name: ", company_name)
#     if len(sanctions) > 0:
#         print("Sanctions: Yes")
#         print(json.dumps(sanctions, indent=4, sort_keys=True))
#     else:
#         print("Sanctions: No")


# main()
