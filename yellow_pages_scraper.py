import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import re
import requests
import os
from bs4 import BeautifulSoup


def extract_email_from_website(url, base_url="https://www.yellowpages.com"):
    try:
        if url.startswith("/"):
            url = f"{base_url}{url}"
            
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, response.text)
        return emails[0] if emails else "Not available"
    except Exception as e:
        print(f"Erreur lors de l'extraction de l'email depuis {url}: {e}")
        return "Not available"

def extract_all(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract Name
        name_element = soup.find("h1", {"class": "business-name"})
        name = name_element.text.strip() if name_element else "Not Available"

        # Extract Address
        address_element = soup.find("span", class_="address")
        address = address_element.text.strip() if address_element else "Not Available"

        # Extract Phone Number
        phone_element = soup.find("a", href=True, class_="phone")
        phone = phone_element["href"].replace("tel:", "+1") if phone_element else "Not Available"

        # Extract Rating
        rating_element = soup.find("div", {"class": "rating"})
        rating = rating_element.text.strip() if rating_element else "Not Available"

        # Extract Reviews
        reviews_element = soup.find("span", {"class": "count"})
        reviews = reviews_element.text.strip() if reviews_element else "Not Available"


        # Extract Social Links
        social_links = [link['href'] for link in soup.find_all('a', href=True) if "facebook.com" in link['href'] or "twitter.com" in link['href']]
        socials = ", ".join(social_links) if social_links else "Not Available"

        # Extract Website
        website_element = soup.find("a", href=True, rel="nofollow")
        website = website_element["href"] if website_element else "Not Available"

        if website != "Not Available" and website.startswith("/"):
            website = f"https://www.yellowpages.com{website}"

        # Extract Email
        email = extract_email_from_website(website)
        #email = ", ".join(set(emails)) if emails else "Not Available"

         # Extract GMAP
        gmap_element = soup.find("a", href=True, class_="general-social-links")
        gmap_url = gmap_element["href"] if gmap_element else "Not Available"

        return {
            "name": name,
            "address": address,
            "phone": phone,
            "email": email,
            "rating": rating,
            "reviews": reviews,
            "other": gmap_url,
            "social": socials,
            "website": website,
        }
    except Exception as e:
        print(f"Error extracting data from {url}: {e}")
        return {
            "name": "Not Available",
            "address": "Not Available",
            "phone": "Not Available",
            "email": "Not Available",
            "other": "Not Available",
            "rating": "Not Available",
            "reviews": "Not Available",
            "social": "Not Available",
            "website": "Not Available",
        }
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--lang=en")
    return webdriver.Chrome(service=Service("/usr/local/bin/chromedriver"), options=chrome_options)

def scrape_yellow_pages(sector, location, max_result=5):
    driver = setup_driver()
    driver.get("https://www.yellowpages.com?hl=en")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "query")))

    # Search for businesses
    search_box = driver.find_element(By.ID, "query")
    search_box_location = driver.find_element(By.ID, "location")
    search_box.clear()
    search_box.send_keys(sector)
    search_box_location.clear()
    search_box_location.send_keys(location)
    search_box.send_keys(Keys.RETURN)

    time.sleep(3)  
    business_data = []
    results_scraped = 0

    visited_urls = set()

    while results_scraped < max_result:
        try:
            # Wait for results to load
            WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='result']")))
            results = driver.find_elements(By.XPATH, "//div[@class='result']")

            for result in results:
                if results_scraped >= max_result:
                    break
                try:
                    ActionChains(driver).move_to_element(result).perform()
                    time.sleep(2) 

                    # Extract link
                    link_element = result.find_element(By.CLASS_NAME, "business-name")
                    full_url = link_element.get_attribute("href")
                    if not full_url or full_url in visited_urls:
                        continue
                    visited_urls.add(full_url)

                    extract = extract_all(full_url)
                    business_data.append({
                        "Name": extract.get("name"),
                        "Address": extract.get("address"),
                        "Phone": extract.get("phone"),
                        "Email": extract.get("email"),
                        "Rating": extract.get("rating"),
                        "Reviews": extract.get("reviews"),
                        "Social": extract.get("social"),
                        "Website": extract.get("website"),
                        "gmap_url": driver.current_url,
                        "other": extract.get("other"),
                    })
                    results_scraped += 1
                except Exception as e:
                    print(f"Error processing result: {e}")
        except Exception as e:
            print(f"Error loading results: {e}")
            break

    
        try:
            next_button = driver.find_elements(By.CLASS_NAME, "next")
            if not next_button or len(next_button) == 0:
                print("No 'Next' button found. Stopping pagination.")
                break
            next_button[0].click()
            time.sleep(5)
        except Exception:
            print("Pagination error or end of results.")
            break
    driver.quit()
    return business_data


def save_data_to_excel(all_data):
    cleaned_data = all_data
    folder_name = "Scraps_data_Final"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    file_name = os.path.join(folder_name, "Data_Generation.xlsx")
    pd.DataFrame(cleaned_data).to_excel(file_name, index=False)
    print(f"Données nettoyées enregistrées dans {file_name}")


if __name__ == "__main__":
    sectors = ["General Contractor","Plumbers"]
    locations = ["Illinois City, IL"]
    all_data = []

    for location in locations:
        for sector in sectors:
            print(f"Scraping {sector} in {location}...")
            data = scrape_yellow_pages(sector, location, max_result=3)
            all_data.extend(data)

    save_data_to_excel(all_data)