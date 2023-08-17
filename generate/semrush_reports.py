import os
import platform
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.conf import settings

def enable_download_in_headless_chrome(browser, download_dir):
    browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
    params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
    browser.execute("send_command", params)

def run_semrush_automation(websites):
    # Input your SemRush Login here
    semrush_mail = "seddalpd@outlook.com"
    semrush_password = "393p247Ter"
    
    
    # Database input + Keep asking until input is in list
    db_input = "us"
    
    # Determine if running on Linux and configure XVFB
    if platform.system() == "Linux":
        from pyvirtualdisplay import Display
        display = Display(visible=0, size=(1920, 1080))
        display.start()
    
    service = ChromeService()
    options = webdriver.ChromeOptions()
    # options.add_argument("--incognito")
    # options.add_argument("--lang=en")
    # options.add_argument("--disable-features=NetworkService")
    # options.add_argument("--window-size=1920,1080")
    browser = webdriver.Chrome(service=service, options=options)

    download_directory = os.path.join(settings.BASE_DIR, 'generate', 'semrush_reports')
    enable_download_in_headless_chrome(browser, download_directory)

    try:
        print('Loading homepage...')
        browser.get("https://www.semrush.com")
        time.sleep(3)
        print('Logging in...')
        browser.get("https://www.semrush.com/login/?src=header&redirect_to=%2F")
        
        # Accept cookies
        cookies = WebDriverWait(browser, 2).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Allow all cookies')]")))
        cookies.click()
        
        print('Inputting login credentials...')
        login_bar = WebDriverWait(browser, 20).until(EC.element_to_be_clickable((By.NAME, "email")))
        login_bar.send_keys(semrush_mail)
        password_bar = WebDriverWait(browser, 20).until(EC.element_to_be_clickable((By.NAME, "password")))
        password_bar.send_keys(semrush_password)
        
        print('Clicking on login button...')
        login_button = WebDriverWait(browser, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="loginForm"]/button[2]')))
        login_button.click()

        time.sleep(5)
        
        for url in websites:
            print('Getting report...')
            browser.get(f"https://semrush.com/analytics/organic/positions/?db={db_input}&searchType=domain&q={url}")
        
            print('Clicking on export icon...')
            export_icon = WebDriverWait(browser, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="igc-ui-kit-68-trigger"]/button')))
            export_icon.click()
            print('Clicking on export to Excel...')
            export_excel = WebDriverWait(browser, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="igc-ui-kit-68-popper"]/div/div/div[3]/button[2]')))
            export_excel.click()
            time.sleep(3)
            print(url + " status: report downloaded")
    
    finally:
        browser.quit()
        if platform.system() == "Linux":
            display.stop()
        print("Done!")

    return websites

# Run the automation function when this script is executed directly
if __name__ == "__main__":
    run_semrush_automation(websites=["thewaterhobby.com","healthline.com"])
