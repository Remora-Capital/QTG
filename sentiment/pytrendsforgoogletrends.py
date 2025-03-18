import os
import pandas as pd
from datetime import datetime, timedelta
import calendar
from pytrends.request import TrendReq
import time
from pytrends.exceptions import TooManyRequestsError

SAVE_FOLDER = "/Users/jaylepore/Documents/GoogleTrendsData"

pytrends = TrendReq(hl='en-US', tz=360)

def fetch_daily_data(kw_list, start_date, end_date, max_retries=5, retry_delay=60):
    timeframe = f"{start_date.strftime('%Y-%m-%d')} {end_date.strftime('%Y-%m-%d')}"
    attempt = 0
    while attempt < max_retries:
        try:
            pytrends.build_payload(kw_list, timeframe=timeframe)
            data = pytrends.interest_over_time()
            if not data.empty and 'isPartial' in data.columns:
                data = data.drop(columns=['isPartial'])
            return data
        except TooManyRequestsError:
            attempt += 1
            print(f"Too many requests error encountered. Retrying in {retry_delay} seconds (attempt {attempt}/{max_retries})")
            time.sleep(retry_delay)
    print("Maximum retries exceeded. Returning empty DataFrame.")
    return pd.DataFrame()

def fetch_and_stitch_year_range(kw_list, start_year, end_year):

    monthly_dfs = []
    prev_overlap = None
    now = datetime.now()
    
    for year in range(start_year, end_year + 1):
        start_month = 1
        end_month = 12
        if year == now.year:
            end_month = now.month
        for month in range(start_month, end_month + 1):
            start_date = datetime(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            end_date = datetime(year, month, last_day, 23, 59)
            print(f"Fetching data for {year}-{month:02d}...")
            
            if not (year == start_year and month == 1):
                overlap_start = start_date - timedelta(days=1)
            else:
                overlap_start = start_date

            data = fetch_daily_data(kw_list, overlap_start, end_date)
            if data.empty:
                print(f"  No data returned for {year}-{month:02d}.")
                continue

            if prev_overlap is not None:
                current_overlap = data.iloc[0]
                for kw in kw_list:
                    if current_overlap[kw] != 0:
                        factor = prev_overlap[kw] / current_overlap[kw]
                        data[kw] = data[kw] * factor
            prev_overlap = data.iloc[-1]
            if not (year == start_year and month == 1):
                data = data.iloc[1:]
            monthly_dfs.append(data)
    
    if monthly_dfs:
        combined_df = pd.concat(monthly_dfs)
        combined_df = combined_df[~combined_df.index.duplicated(keep='first')]
        combined_df.sort_index(inplace=True)
        return combined_df
    else:
        return pd.DataFrame()

def main():
    keywords = input("Enter keyword(s) for Google Trends search (separate multiple keywords with commas): ").strip()
    kw_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
    if not kw_list:
        print("No valid keywords provided. Exiting.")
        return

    start_year_input = input("Enter the start year (YYYY): ").strip()
    end_year_input = input("Enter the end year (YYYY): ").strip()
    try:
        start_year = int(start_year_input)
        end_year = int(end_year_input)
    except ValueError:
        print("Invalid year provided. Exiting.")
        return
    if start_year > end_year:
        print("Start year must be less than or equal to end year. Exiting.")
        return

    save_option = input("Choose saving option:\n"
                        "1. All data in a single combined CSV file\n"
                        "2. Separate CSV files for each month\n"
                        "Enter 1 or 2: ").strip()
    if save_option not in ['1', '2']:
        print("Invalid option. Exiting.")
        return

    print(f"Fetching Google Trends daily data for {', '.join(kw_list)} from {start_year} to {end_year} ...")
    combined_data = fetch_and_stitch_year_range(kw_list, start_year, end_year)
    if combined_data.empty:
        print("No data returned from Google Trends.")
        return
    else:
        print("Data fetching complete.")

    if not os.path.exists(SAVE_FOLDER):
        os.makedirs(SAVE_FOLDER)
        print(f"Folder '{SAVE_FOLDER}' created.")

    if save_option == '1':
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(SAVE_FOLDER, f"google_trends_{start_year}_{end_year}_{timestamp}.csv")
        combined_data.to_csv(filename)
        print(f"Combined data saved to {filename}")
    else:
        for year in range(start_year, end_year + 1):
            start_month = 1
            end_month = 12
            if year == datetime.now().year:
                end_month = datetime.now().month
            for month in range(start_month, end_month + 1):
                month_str = f"{year}-{month:02d}"
                df_month = combined_data[combined_data.index.strftime("%Y-%m") == month_str]
                if not df_month.empty:
                    filename = os.path.join(SAVE_FOLDER, f"google_trends_{year}_{month:02d}.csv")
                    df_month.to_csv(filename)
                    print(f"Data for {month_str} saved to {filename}")

if __name__ == '__main__':
    main()
