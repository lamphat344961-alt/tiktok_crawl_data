from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import time
import pandas as pd
import random
import re
import os

# --- 1. CẤU HÌNH ---
MY_PROFILE_PATH = r"c:\Users\Admin\AppData\Roaming\Mozilla\Firefox\Profiles\3k9cekk1.default-release"
GECKO_PATH = r"C:\Users\Admin\Desktop\TANPHAT\Manguonmotrongkhoahocjdulieu\DOAN_MNM\tiktok\geckodriver.exe"
FIREFOX_BINARY_PATH = r"C:\Program Files\Mozilla Firefox\firefox.exe"



# --- 3. KHỞI TẠO DRIVER ---
ser = Service(GECKO_PATH)
options = webdriver.firefox.options.Options()
options.binary_location = FIREFOX_BINARY_PATH
options.add_argument("-profile")
options.add_argument(MY_PROFILE_PATH)
options.set_preference("dom.webdriver.enabled", False)
options.set_preference("useAutomationExtension", False)

driver = None 

print("WARNING: Hãy TẮT HOÀN TOÀN Firefox thật trước khi chạy!")
print("Đang khởi động Firefox với Profile cá nhân...")

driver = webdriver.Firefox(options=options, service=ser)
wait = WebDriverWait(driver, 20)
action = ActionChains(driver)


def random_sleep(min_s=2, max_s=5):
    """Ngủ ngẫu nhiên để giống người"""
    sleep_time = random.uniform(min_s, max_s)
    print(f"   ...Nghỉ {sleep_time:.2f}s...")
    time.sleep(sleep_time)

def human_scroll_virtual_container(driver, wait, moves=6):
    container = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.virtualCardResults")
        )
    )
    for i in range(moves):
        # khoảng scroll giống người
        dy = random.randint(300, 900)
        before = driver.execute_script(
            "return arguments[0].scrollTop;", container
        )
        # scroll trực tiếp container
        driver.execute_script(
            "arguments[0].scrollTop += arguments[1];",
            container, dy
        )
        time.sleep(random.uniform(0.6, 1.5))
        after = driver.execute_script(
            "return arguments[0].scrollTop;", container
        )
        # cuộn ngược nhẹ (giống người đọc lại)
        if random.random() < 0.15:
            back = random.randint(100, 250)
            driver.execute_script(
                "arguments[0].scrollTop -= arguments[1];",
                container, back
            )
            time.sleep(random.uniform(0.4, 0.9))

# Vào trang Ads
target_url = "https://ads.tiktok.com/creative/forpartners/creator/explore?region=row"
print(f"Truy cập: {target_url}")
driver.get(target_url)
driver.maximize_window()
time.sleep(5) 
print("Tiêu đề trang hiện tại:", driver.title)
human_scroll_virtual_container(driver, wait, moves=random.randint(6, 10))
