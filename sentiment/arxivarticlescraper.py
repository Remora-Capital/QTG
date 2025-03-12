import os
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote
from datetime import datetime
import calendar

SAVE_FOLDER = "/Users/jaylepore/Library/CloudStorage/Box-Box/Web Scraping Data"

def fetch_articles_date_range(keywords, start_date, end_date, start=0, max_results=2000):
    start_str = start_date.strftime("%Y%m%d") + "0000"
    end_str = end_date.strftime("%Y%m%d") + "2359"
    date_query = f"submittedDate:[{start_str} TO {end_str}]"
    query = f'((ti:"{keywords}" OR abs:"{keywords}")) AND {date_query}'
    base_url = "http://export.arxiv.org/api/query?"
    url = (f"{base_url}search_query={quote(query)}"
           f"&start={start}&max_results={max_results}"
           f"&sortBy=submittedDate&sortOrder=descending")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching data from arXiv API (status code: {response.status_code})")
        return None, 0
    root = ET.fromstring(response.text)
    ns = {
        'atom': 'http://www.w3.org/2005/Atom',
        'opensearch': 'http://a9.com/-/spec/opensearch/1.1/'
    }
    total_results_tag = root.find('opensearch:totalResults', ns)
    total_results = int(total_results_tag.text) if total_results_tag is not None else 0
    entries = root.findall('atom:entry', ns)
    articles = []
    for entry in entries:
        published_text = entry.find('atom:published', ns).text
        try:
            published_date = datetime.strptime(published_text, "%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            continue
        full_id = entry.find('atom:id', ns).text.strip()
        arxiv_id = full_id.split('/abs/')[-1]
        title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
        authors = [author.find('atom:name', ns).text.strip() for author in entry.findall('atom:author', ns)]
        articles.append({
            "id": arxiv_id,
            "title": title,
            "authors": authors,
            "published": published_text,
            "published_date": published_date,
            "link": full_id.replace("/abs/", "/pdf/")
        })
    return articles, total_results

def main():
    keywords = input("Enter keyword(s) for search (applied to title and abstract): ").strip()
    save_option = input("Choose saving option:\n1. All articles in a single combined file\n2. Separate files for each article\nEnter 1 or 2: ").strip()
    if save_option not in ['1', '2']:
        print("Invalid option. Exiting.")
        return
    start_year = 2019
    current_date = datetime.now()
    end_year = current_date.year
    all_articles = []
    for year in range(start_year, end_year + 1):
        start_month = 1
        end_month = 12
        if year == end_year:
            end_month = current_date.month
        for month in range(start_month, end_month + 1):
            start_date = datetime(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            end_date = datetime(year, month, last_day, 23, 59)
            print(f"Fetching articles for {year}-{month:02d}...")
            batch_size = 2000
            batch, total_results = fetch_articles_date_range(keywords, start_date, end_date, start=0, max_results=batch_size)
            if batch is None:
                continue
            print(f"  API reports {total_results} result(s) for {year}-{month:02d}.")
            current_start = 0
            while current_start < total_results:
                batch, _ = fetch_articles_date_range(keywords, start_date, end_date, start=current_start, max_results=batch_size)
                if batch is None or not batch:
                    break
                all_articles.extend(batch)
                current_start += batch_size
    unique_articles = {article["id"]: article for article in all_articles}.values()
    unique_articles = list(unique_articles)
    total_found = len(unique_articles)
    print(f"\nCollected {total_found} unique article(s) matching your keywords.")
    if total_found == 0:
        print("No articles found matching the criteria.")
        return
    confirm = input("Do you want to download these articles? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Download cancelled.")
        return
    if not os.path.exists(SAVE_FOLDER):
        os.makedirs(SAVE_FOLDER)
        print(f"Folder '{SAVE_FOLDER}' created.")
    
    if save_option == '1':
        print("Combined articles option is not supported for PDF downloads. Saving as separate PDF files.")

    for article in unique_articles:
        safe_id = article["id"].replace("/", "_")
        pdf_filename = os.path.join(SAVE_FOLDER, f"{safe_id}.pdf")
        print(f"Downloading PDF for {article['id']}...")
        pdf_response = requests.get(article["link"])
        if pdf_response.status_code == 200:
            with open(pdf_filename, "wb") as f:
                f.write(pdf_response.content)
            print(f"Saved PDF: {pdf_filename}")
        else:
            print(f"Failed to download PDF for {article['id']} (status code: {pdf_response.status_code})")
    
    print(f"Download complete. {len(unique_articles)} PDF file(s) saved in '{SAVE_FOLDER}'.")

if __name__ == '__main__':
    main()
