# Yellow Pages Scraper

A Python script to scrape business information from **Yellow Pages**. The script uses `Selenium` and `BeautifulSoup` to extract details like business name, address, phone number, email, social media links, reviews, and ratings. The scraped data is saved into an Excel file.

## Features
- Scrapes business details including:
  - Business Name
  - Address
  - Phone Number
  - Email
  - Social Media Links (Facebook, Twitter)
  - Reviews
  - Ratings
- Supports pagination to extract multiple pages of results.
- Saves the cleaned data to an Excel file for easy analysis.

## Requirements
- Python 3.7 or higher
- Google Chrome
- ChromeDriver (ensure it matches your Chrome version)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/keichk/yellow-pages-scraper.git
   cd yellow-pages-scraper
