import os
import unittest
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from config.constant import LANGUAGE_SETTINGS, CREDENTIALS, PROFILE_URL
from tests.authentication_test.base_test import BaseTest
import tempfile
import requests
from urllib.parse import urlparse

class TestProfilePage(BaseTest):

    def __init__(self, methodName="runTest", language=None, browser=None):
        super().__init__(methodName)
        self.language = language
        self.browser = browser
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        file_handler = logging.FileHandler("test_profile_output.log")
        file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

        self.logger.propagate = False

    def setUp(self):
        if not self.browser or not self.language:
            raise ValueError("Browser or language is not set.")
        self.logger.info(f"Setting up {self.browser} browser for {self.language} language...")
        self.driver = self.initialize_browser(self.browser)
        self.url = LANGUAGE_SETTINGS[self.language]["home_url"]
        self.driver.get(self.url)
        # self.driver.maximize_window()
        self.driver.set_window_size(375, 812)
        self.navigate_to_login_page()
        self.perform_login(CREDENTIALS["duplicated_user"]["username"], CREDENTIALS["duplicated_user"]["password"])
        self.navigate_to_profile_page(self.language)

    def tearDown(self):
        if hasattr(self, "driver"):
            self.driver.quit()

    def verify_upload_success(self, isFromGallery = True):
        driver = self.driver

        try:
            profile_img_before = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'img[alt="profile_avatar"]'))
            )
            img_src_before = profile_img_before.get_attribute("src")
            self.logger.info(f"Profile image src before upload: {img_src_before}")

            if isFromGallery:
                upload_success = self.upload_from_gallery()
                if not upload_success:
                    self.logger.error("Image upload failed.")
                    return False
            else:
                self.driver.maximize_window()
                upload_success = self.upload_from_camera()
                self.driver.set_window_size(375, 812)
                if not upload_success:
                    self.logger.error("Image upload failed.")
                    return False
                

            self.logger.info("Waiting for upload to complete...")
            time.sleep(10)
            self.success_box()
            driver.refresh()
            self.logger.info("Page refreshed.")

            profile_img_after = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'img[alt="profile_avatar"]'))
            )
            sm_img_src_after = profile_img_after.get_attribute("src")
            self.logger.info(f"Small profile image src after upload: {sm_img_src_after}")
            
            lg_img_src_after = profile_img_after.get_attribute("src")
            self.logger.info(f"Large profile image src after upload: {lg_img_src_after}")

            if sm_img_src_after != img_src_before and sm_img_src_after:
                self.logger.info("Profile picture updated successfully with a new blob URL.")
                if sm_img_src_after == lg_img_src_after:
                    self.logger.info("Small profile picture and large profile picture is same.")
                    return True

            self.logger.warning("Profile picture URL did not change or is not a blob URL.")
            return False

        except (TimeoutException, NoSuchElementException) as e:
            self.logger.error(f"Verification failed: {str(e)}")
            return False
    
    def verify_invalid_format_upload(self):
        driver = self.driver
        try:
            # Find file input element
            file_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="file"]'))
            )
            
            # Upload invalid format file
            invalid_file_url = PROFILE_URL["invalid_format_url"]
            # Get the filename from URL
            filename = os.path.basename(urlparse(invalid_file_url).path)
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
                try:
                    response = requests.get(invalid_file_url)
                    response.raise_for_status()  # Raises an HTTPError for bad responses
                    temp_file.write(response.content)
                    invalid_file_path = temp_file.name
                except requests.exceptions.RequestException as e:
                    self.fail(f"Failed to download image from URL: {e}")
                    return False

            if not os.path.exists(invalid_file_path):
                raise FileNotFoundError(f"Test image not found at {invalid_file_path}")
            
            file_input.send_keys(invalid_file_path)
            self.logger.info(f"Attempting to upload invalid file: {invalid_file_path}")

            self.warning_box()
            self.logger.info("Error message disappeared as expected")
            return True

        except Exception as e:
            self.logger.error(f"Invalid format upload verification failed: {str(e)}")
            return False

    def test_01_ChangeProfileGallery(self):
        driver = self.driver

        try:
            # upload
            self.logger.info("Starting gallery upload test...")
            edit_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.MuiButtonBase-root.MuiIconButton-root"))
            )
            edit_button.click()
            verification_success = self.verify_upload_success(True)
            self.assertTrue(verification_success, "Failed to verify profile picture update")

        except Exception as e:
            self.fail(f"Test failed with error: {str(e)}")
    
    def test_02_ChangeProfileCamera(self):
        driver = self.driver

        try:
            # camera
            self.logger.info("Starting camera upload test...")
            edit_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.MuiButtonBase-root.MuiIconButton-root"))
            )
            edit_button.click()
            verification_success = self.verify_upload_success(False)
            self.assertTrue(verification_success, "Failed to verify profile picture update")
        except Exception as e:
            self.fail(f"Test failed with error: {str(e)}")
    
    def test_03_ChangeProfileInvalidFormat(self):
        driver = self.driver

        try:
            #invalid format
            self.logger.info("Starting invalid format upload test...")
            edit_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.MuiButtonBase-root.MuiIconButton-root"))
            )
            edit_button.click()
            verification_success = self.verify_invalid_format_upload()
            self.assertTrue(verification_success, "Failed to verify invalid format upload")
        except Exception as e:
            self.fail(f"Test failed with error: {str(e)}")
    
    def test_04_ChangeProfileLargeFile(self):
        driver = self.driver

        try:
            # Large File
            self.logger.info("Starting large file upload test...")
            edit_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.MuiButtonBase-root.MuiIconButton-root"))
            )
            edit_button.click()
            self.upload_from_gallery(checkLargeFile=True)
            self.check_general_error(LANGUAGE_SETTINGS[self.language]["errors"]["large_file_type"], id="swal2-title")
        except Exception as e:
            self.fail(f"Test failed with error: {str(e)}")

if __name__ == "__main__":
    unittest.main()
