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

def safe_click(driver, xpath, retries=5):
    """
    Cố gắng tìm và click phần tử. Nếu gặp lỗi Stale (phần tử bị thay đổi),
    nó sẽ tự tìm lại và click tiếp.
    """
    for i in range(retries):
        try:
            # 1. Tìm lại phần tử (Phải tìm lại trong vòng lặp mới khắc phục được Stale)
            element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, xpath)))
            # 2. Scroll tới nó
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(1) 
            # 3. Click bằng JS
            driver.execute_script("arguments[0].click();", element)
            print(f"   -> Click thành công: {xpath}")
            return True
        except StaleElementReferenceException:
            print(f"   [Cảnh báo] Lỗi Stale (lần {i+1}). Đang tìm lại phần tử...")
            time.sleep(1.5) # Chờ DOM ổn định lại
        except Exception as e:
            # Nếu chưa tìm thấy, chờ thêm chút ở các vòng lặp đầu
            time.sleep(1)
            if i == retries - 1:
                print(f"   [Lỗi] Không thể click sau {retries} lần thử: {e}")
    return False

# =================================================================================
# PHẦN 1: CHỌN QUỐC GIA -> VIỆT NAM
# =================================================================================
# 1. Mở menu Quốc gia
# Tìm nút có class filter-trigger đầu tiên hoặc chứa text 'Quốc gia'
trigger_xpath = "//div[contains(@class,'filter-trigger')][1]" 

if safe_click(driver, trigger_xpath):
    print("Đã mở menu Quốc gia.")
    time.sleep(2) # Chờ menu bung ra hoàn toàn
    # 2. Chọn Việt Nam (
    # XPath tìm thẻ div chứa text "Việt Nam"
    vn_xpath = "//div[contains(@class, 'truncated__text') and text()='Việt Nam']"
    is_clicked = safe_click(driver, vn_xpath)
    if is_clicked:
        print("Đã chọn 'Việt Nam'.")
        time.sleep(1)
    else:
        print("KHÔNG THỂ click 'Việt Nam'. Kiểm tra lại XPath.")
else:
    print("Không mở được menu Quốc gia.")

time.sleep(3) # Đợi trang load lại dữ liệu

price_trigger_xpath = "//div[contains(@class, 'filter-item-menu-label') and .//p[contains(text(), 'Giá')]]"
# Nếu không tìm thấy bằng class, dùng XPath dự phòng tìm theo text đơn giản
backup_trigger_xpath = "//p[text()='Giá']/ancestor::div[contains(@class, 'filter-item-menu-label')]"
if safe_click(driver, price_trigger_xpath) or safe_click(driver, backup_trigger_xpath):
    print("Đã mở menu Giá.")
    time.sleep(2) # Chờ menu bung ra

    # 2. Chọn "> 300 USD"
    price_option_xpath = "//li[contains(@class, 'filter-form-select__item') and contains(text(), '> 300 USD')]"
    is_price_clicked = safe_click(driver, price_option_xpath)
    
    if is_price_clicked:
        apply_xpath = "//button[contains(text(), 'Áp dụng')]"
        safe_click(driver, apply_xpath)
        print("Đã bấm Áp dụng.")
    else:
        print("Không tìm thấy text '> 300 USD', thử chọn mục cuối cùng...")

    # 3. Đóng menu
    time.sleep(1)
    try:
        # Click vào khoảng trống bên phải nút Giá (move offset) hoặc click body
        action.move_by_offset(200, 0).click().perform()
    except:
        pass

else:
    print("LỖI: Không tìm thấy nút bấm 'Giá' (Class: filter-item-menu-label).")

human_scroll_virtual_container(driver, wait, moves=random.randint(6, 10))
time.sleep(2)
