"""
Function libary containing scripts to extract digital identity related stats from the company website
"""
import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from seoanalyzer import analyze
import requests
from selenium import webdriver



def extract_seo_stats(website_url) -> dict:
    return analyze(website_url, analyze_extra_tags=True, analyze_headings=True, follow_links=False)


def extract_linkedin_stats(driver, linkedin_url) -> int:
    driver.get(linkedin_url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    #followers = soup.find('p', {'class': '!text-xs text-color-text-low-emphasis leading-[1.33333] m-0 truncate'})
    followers_elements = driver.find_elements(By.CSS_SELECTOR, "h3.top-card-layout__first-subline")

    followers = None
    if len(followers_elements) > 0:
        followers = followers_elements[0].text.strip()

    if followers is None:
        raise RuntimeError(f"Failed to extract the LinkedIn Followers text from the url {linkedin_url}. "
                           f"Follower Text not found. Page displayed is {driver.current_url}  with title '{driver.title}'")

    followers_parts = followers.split(" ")
    if len(followers_parts) > 1:
        followers = followers_parts[len(followers_parts)-2].strip().replace(",", "")
    else:
        followers = ""

    if len(followers) > 0:
        return int(followers)
    else:
        raise RuntimeError(f"Failed to extract the LinkedIn followers for page {linkedin_url}"
                           f"Page displayed is {driver.current_url}  with title '{driver.title}'")
