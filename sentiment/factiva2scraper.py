import time
import logging
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


URL = 'https://wlu.primo.exlibrisgroup.com/view/action/uresolver.do?operation=resolveService&package_service_id=7736284540004161&institutionId=4161&customerId=4160&VE=true'
SEARCH_TERM = "APPL"
USERNAME = ""
PASSWORD = ""
START_DATE = "01012021"
END_DATE = "01012022"
TIMEOUT = 20
RETRY_LIMIT = 3

output = []

def good_click(driver, by, identifier, description, hover = False):
    for attempt in range(RETRY_LIMIT):
        try:
            element = WebDriverWait(driver, TIMEOUT).until(
                EC.element_to_be_clickable((by, identifier))
            )
            if hover:
                time.sleep(1)
                webdriver.ActionChains(driver).move_to_element(element).perform()
                time.sleep(1)
            element.click()
            logging.info(f"Clicked {description}.")
            return True
        except Exception as e:
            logging.error(f"Error clicking {description}: {e} (Attempt {attempt+1}/{RETRY_LIMIT})")
            time.sleep(2)
    return False

def good_send_keys(driver, by, identifier, keys, description, clear=True):
    for attempt in range(RETRY_LIMIT):
        try:
            element = WebDriverWait(driver, TIMEOUT).until(
                EC.visibility_of_element_located((by, identifier))
            )
            if clear:
                element.clear()
            element.send_keys(keys)
            logging.info(f"Sent keys to {description}.")
            return True
        except Exception as e:
            logging.error(f"Error sending keys to {description}: {e} (Attempt {attempt+1}/{RETRY_LIMIT})")
            time.sleep(2)
    return False

def initial_setup(driver):
    driver.get(URL)
    logging.info(f"Navigated to {URL}")
    try:
        # Login to WLU

        if not good_send_keys(driver, By.ID, 'input28', USERNAME, "Username"):
            return False
        
        if not good_send_keys(driver, By.ID, 'input36', PASSWORD, "Password"):
            return False

        if not good_click(driver, By.XPATH, '//*[@id="form20"]/div[2]/input', "Sign In"):
            return False


        # Set up Factiva search

        if not good_click(driver, By.XPATH, '//*[@id="navmbm16"]/a', "Switch Factiva"):
            return False
        
        if not good_click(driver, By.XPATH, '/html/body/div[1]/div/div/div[2]/div/div[2]/div[2]/header/div/div[1]/div/div/form/div/div[2]/div/button', "Search Settings", hover=True):
            return False

        if not good_click(driver, By.XPATH, '/html/body/div[1]/div/div/div[2]/div/div[2]/div[2]/header/div/div[1]/div/div/form/div/div[2]/div/div/div/div/div/div/div[2]/button', "Date Range", hover=True):
            return False

        if not good_click(driver, By.XPATH, '/html/body/div[1]/div/div/div[2]/div/div[2]/div[2]/header/div/div[1]/div/div/form/div/div[2]/div/div/div/div/div/div/div[2]/div[3]/div/div/div/div/div[9]/button', "Custom Date"):
            return False

        for char in START_DATE:
            if not good_send_keys(driver, By.XPATH, '/html/body/div[1]/div/div/div[2]/div/div[2]/div[2]/header/div/div[1]/div/div/form/div/div[2]/div/div/div/div/div/div/div[2]/div[3]/div[1]/div/input', char, "Start Date", clear=False):
                return False

            time.sleep(0.1)

        for char in END_DATE:
            if not good_send_keys(driver, By.XPATH, '/html/body/div[1]/div/div/div[2]/div/div[2]/div[2]/header/div/div[1]/div/div/form/div/div[2]/div/div/div/div/div/div/div[2]/div[3]/div[2]/div/input', char, "End Date", clear=False):
                return False

            time.sleep(0.1)


        if not good_click(driver, By.XPATH, '/html/body/div[1]/div/div/div[2]/div/div[2]/div[2]/header/div/div[1]/div/div/form/div/div[2]/div/div/div/div/div/div/div[2]/div[4]/button[2]', "Apply Date Range"):
            return False
        
        if not good_click(driver, By.ID, 'dj-combobox-input', "Search bar", hover=True):
            return False
        
        if not good_send_keys(driver, By.ID, 'dj-combobox-input', SEARCH_TERM, "Search bar"):
            return False
        
        time.sleep(2)
        
        if not good_click(driver, By.ID, 'dj-combobox-item-1', "First search suggestion"):
            return False


        return True

    except Exception as e:
        logging.error(f"Error in initial setup: {e}")
        return False
    

def process_page(driver):
    if not good_click(driver, By.XPATH, '/html/body/div[1]/div/div/div[2]/div/div[2]/div[3]/div/div/div/div/div[6]/div/div[2]/div/div/div[1]/div[3]/div/div[2]/div[1]/div/div/div/div[1]/div[1]/div/div/div[2]/h3/span', "First article"):
        return False
    
    for i in range(20):
        title_element = WebDriverWait(driver, TIMEOUT).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'headline__StyledHeadlineWrapper-sc-1xf566w-0'))
        )
        title = title_element.text 

        meta_element = WebDriverWait(driver, TIMEOUT).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'meta-data__MetaWrapper-sc-okrr8s-0'))
        )
        meta = meta_element.text

        text_element = WebDriverWait(driver, TIMEOUT).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'body-paragraph__BodyParagraphWrapper-sc-1c0tve-0'))
        )
        text = text_element.text

        output.append({'title': title, 'meta': meta, 'text': text})
        if i != 19:
            if not good_click(driver, By.XPATH, '/html/body/div[1]/div/div/div[2]/div/div[2]/div[3]/div/div/div/div[1]/div/div[2]/div/button[2]', "Next article"):
                return False
        else:
            if not good_click(driver, By.XPATH, '/html/body/div[1]/div/div/div[2]/div/div/div[3]/div/div/div/div[1]/div/button', "Back to search results"):
                return False
            
    return True
            

def processer(driver, page_number):

    logging.info(f"Processing page {page_number}")


    
    while True:
        if not process_page(driver):
            return False
        if not good_click(driver, By.XPATH, '/html/body/div[1]/div/div/div[2]/div/div/div[3]/div/div/div/div/div[6]/div/div[2]/div/div/div[1]/div[3]/div/div[2]/div[2]/div[2]/div/button[2]', "Next page"):
            return False
    
    
    logging.info(f"Page {page_number} processed successfully.")
    return True

def main():
    try:
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)

        if not initial_setup(driver):
            logging.error("Initial setup failed. Exiting script.")
            driver.quit()
            return

        page = 1
        while True:
            if not processer(driver, page):
                logging.error(f"Processing page {page} failed. Exiting loop.")
                break

            try:
                driver.find_element(By.ID, 'next_100')
                page += 1
                time.sleep(2)
            except NoSuchElementException:
                logging.info("No more pages available. Ending process.")
                break
        print(output)
        driver.quit()
        logging.info("Automation script completed successfully.")

    except Exception as e:
        json.dump(output, open('./output.json', 'w'))        
        logging.error(f"Fatal error in main script: {e}")

if __name__ == '__main__':
    main()
