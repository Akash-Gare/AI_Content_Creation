import time
import os
import logging
from functools import wraps
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from app.config import INSTAGRAM_URL, CHROME_PROFILE_PATH
from app.utils.logger import get_logger

logger = get_logger(__name__)

def retry_posting(max_retries=2, delay=5):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Post failed after {max_retries} retries: {e}")
                        raise e
                    logger.warning(f"Post failed, retrying ({retries}/{max_retries}) in {delay}s... Error: {e}")
                    time.sleep(delay)
            return False
        return wrapper
    return decorator

@retry_posting(max_retries=2)
def post_to_instagram(image_path: str, caption: str):
    """
    Automates Instagram posting using Selenium.
    Uses Chrome profile for persistent login.
    """
    options = Options()
    if CHROME_PROFILE_PATH:
        # e.g., C:/Users/Name/AppData/Local/Google/Chrome/User Data
        user_data_dir = os.path.dirname(CHROME_PROFILE_PATH)
        profile_name = os.path.basename(CHROME_PROFILE_PATH)
        options.add_argument(f"--user-data-dir={user_data_dir}")
        options.add_argument(f"--profile-directory={profile_name}")
    
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    # Do NOT use headless mode as per requirements
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 20)
    
    try:
        logger.info(f"Opening Instagram: {INSTAGRAM_URL}")
        driver.get(INSTAGRAM_URL)
        
        # Check if login is needed (Wait for 'Create' button or login fields)
        try:
            # Look for the 'Create' button (often an SVG with aria-label or just a specific div)
            create_btn_xpath = "//button[contains(., 'Create')] | //span[text()='Create'] | //a[@href='#']//div[contains(text(), 'Create')]"
            wait.until(EC.presence_of_element_located((By.XPATH, create_btn_xpath)))
            logger.info("Logged in successfully (or session active).")
        except TimeoutException:
            logger.warning("Session not detected. Please log in manually if the login screen appears.")
            # Wait longer for manual login if needed
            wait_manual = WebDriverWait(driver, 60)
            wait_manual.until(EC.presence_of_element_located((By.XPATH, create_btn_xpath)))
            logger.info("Manual login detected.")

        # 1. Click 'Create'
        create_btn = driver.find_element(By.XPATH, create_btn_xpath)
        create_btn.click()
        logger.info("Clicked 'Create' button.")

        # 2. Upload image
        # Wait for file input
        file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
        abs_path = os.path.abspath(image_path)
        file_input.send_keys(abs_path)
        logger.info(f"Uploaded image: {abs_path}")

        # 3. Click 'Next' (Crop/Select screen)
        next_btn_xpath = "//div[@role='button' and text()='Next']"
        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, next_btn_xpath)))
        next_btn.click()
        logger.info("First 'Next' clicked.")

        # 4. Click 'Next' (Filter screen)
        next_btn2 = wait.until(EC.element_to_be_clickable((By.XPATH, next_btn_xpath)))
        next_btn2.click()
        logger.info("Second 'Next' clicked.")

        # 5. Add caption
        caption_area = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[aria-label='Write a caption...']")))
        caption_area.click() # Focus
        driver.execute_script("arguments[0].innerText = arguments[1];", caption_area, caption)
        # Sometimes innerText isn't enough for the submit button to enable, let's try send_keys too
        caption_area.send_keys(" ") 
        logger.info("Caption added.")

        # 6. Click 'Share'
        share_btn_xpath = "//div[@role='button' and text()='Share']"
        share_btn = wait.until(EC.element_to_be_clickable((By.XPATH, share_btn_xpath)))
        share_btn.click()
        logger.info("Clicked 'Share'.")

        # 7. Wait for completion
        # Check for 'Your post has been shared' or similar
        success_msg_xpath = "//span[contains(text(), 'Your post has been shared')]"
        wait.until(EC.presence_of_element_located((By.XPATH, success_msg_xpath)))
        logger.info("Post shared successfully!")
        
        return True

    except Exception as e:
        logger.error(f"Error during posting: {e}")
        driver.save_screenshot(f"logs/error_post_{int(time.time())}.png")
        raise e
    finally:
        driver.quit()

if __name__ == "__main__":
    # Test call
    import sys
    if len(sys.argv) > 2:
        post_to_instagram(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python instagram.py <image_path> <caption text>")
