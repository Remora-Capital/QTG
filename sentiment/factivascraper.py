import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


logging.basicConfig(
    filename='logger',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


URL = 'https://search.worldcat.org/libraries/4036'
SEARCH_TERM = "2574-9579"
EMAIL_ADDRESS = "Factiva.hbya1au71hsgiw7f@u.box.com"
TIMEOUT = 20
RETRY_LIMIT = 3

def good_click(driver, by, identifier, description):
    for attempt in range(RETRY_LIMIT):
        try:
            element = WebDriverWait(driver, TIMEOUT).until(
                EC.element_to_be_clickable((by, identifier))
            )
            element.click()
            logging.info(f"Clicked {description}.")
            return True
        except Exception as e:
            logging.error(f"Error clicking {description}: {e} (Attempt {attempt+1}/{RETRY_LIMIT})")
            time.sleep(2)
    return False

def good_send_keys(driver, by, identifier, keys, description):
    for attempt in range(RETRY_LIMIT):
        try:
            element = WebDriverWait(driver, TIMEOUT).until(
                EC.visibility_of_element_located((by, identifier))
            )
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

        if not good_click(driver, By.ID, 'go_to_catalogue', "Go to Library's Catalogue button"):
            return False

        if not good_click(driver, By.ID, 'login_button', "Login button"):
            return False

        if not good_send_keys(driver, By.ID, 'search_bar', SEARCH_TERM, "Search bar"):
            return False

        if not good_click(driver, By.ID, 'factiva_box', "Factiva box (from 1979)"):
            return False

        if not good_click(driver, By.ID, 'search_button', "Search button"):
            return False

        return True

    except Exception as e:
        logging.error(f"Error in initial setup: {e}")
        return False

def process_page(driver, page_number):
    """
      1. Press "Select All".
      2. Press "Email" (gotta do the captcha thing here).
      3. Press "Continue".
      4. Enter the "Email To:" address.
      5. Press "Email Output: HTML".
      6. Press "Plain Text".
      7. Press "Send".
      8. Press "OK".
      9. Press "Next 100".
     10. Press "Clear".

    """
    logging.info(f"Processing page {page_number}")

    if not good_click(driver, By.ID, 'select_all', "Select All checkbox"):
        return False

    if not good_click(driver, By.ID, 'email_button', "Email button"):
        return False

    if not good_click(driver, By.ID, 'continue_button', "Continue button"):
        return False

    if not good_send_keys(driver, By.ID, 'email_to', EMAIL_ADDRESS, "Email To field"):
        return False

    if not good_click(driver, By.ID, 'email_output_html', "Email Output: HTML button"):
        return False

    if not good_click(driver, By.ID, 'plain_text', "Plain Text button"):
        return False

    if not good_click(driver, By.ID, 'send_button', "Send button"):
        return False

    if not good_click(driver, By.ID, 'ok_button', "OK button"):
        return False

    if not good_click(driver, By.ID, 'next_100', "Next 100 button"):
        return False

    if not good_click(driver, By.ID, 'clear_button', "Clear button"):
        return False

    logging.info(f"Page {page_number} processed successfully.")
    return True

def main():
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)

        if not initial_setup(driver):
            logging.error("Initial setup failed. Exiting script.")
            driver.quit()
            return

        page = 1
        while True:
            if not process_page(driver, page):
                logging.error(f"Processing page {page} failed. Exiting loop.")
                break

            try:
                driver.find_element(By.ID, 'next_100')
                page += 1
                time.sleep(2)
            except NoSuchElementException:
                logging.info("No more pages available. Ending process.")
                break

        driver.quit()
        logging.info("Automation script completed successfully.")

    except Exception as e:
        logging.error(f"Fatal error in main script: {e}")

if __name__ == '__main__':
    main()
