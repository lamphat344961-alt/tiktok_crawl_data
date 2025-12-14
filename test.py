import time
import random
import os
import pandas as pd

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.action_chains import ActionChains


# =============================================================================
# 1. CẤU HÌNH (HÃY SỬA ĐƯỜNG DẪN CỦA BẠN TẠI ĐÂY)
# =============================================================================
MY_PROFILE_PATH = r"c:\Users\Admin\AppData\Roaming\Mozilla\Firefox\Profiles\3k9cekk1.default-release"
GECKO_PATH = r"C:\Users\Admin\Desktop\TANPHAT\Manguonmotrongkhoahocjdulieu\DOAN_MNM\tiktok\geckodriver.exe"
FIREFOX_BINARY_PATH = r"C:\Program Files\Mozilla Firefox\firefox.exe"

TARGET_CREATOR_COUNT = 5  # Số lượng Creator muốn cào
OUTPUT_FILE = "tiktok_creators_final.xlsx"
TARGET_URL = "https://ads.tiktok.com/creative/forpartners/creator/explore?region=row"


# =============================================================================
# 2. CÁC HÀM HỖ TRỢ (UTILS)
# =============================================================================
def safe_click(driver, xpath, retries=5):
    """
    Click an toàn chống lỗi StaleElement.
    Lưu ý: ưu tiên click thật trong tương lai; JS click dùng tốt cho filter/menu.
    """
    for _ in range(retries):
        try:
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
            time.sleep(random.uniform(0.4, 0.9))
            driver.execute_script("arguments[0].click();", element)
            return True
        except (StaleElementReferenceException, TimeoutException):
            time.sleep(random.uniform(0.6, 1.2))
        except Exception:
            time.sleep(random.uniform(0.6, 1.2))
    return False


def extract_card_data(card_element):
    """
    Trích xuất dữ liệu chi tiết từ 1 thẻ Creator (ổn định cho virtual list TikTok).
    """
    info = {
        "Name": "N/A",
        "Collab Score": "N/A",
        "Followers": "N/A",
        "Median Views": "N/A",
        "Engagement": "N/A",
        "Start Price": "N/A",
        "Tags (Colored)": ""
    }

    # ------------------------------------------------------------------
    # 1) NAME
    # ------------------------------------------------------------------
    try:
        info["Name"] = card_element.find_element(
            By.CSS_SELECTOR, ".truncated__text-single"
        ).text.strip()
    except Exception:
        pass

    # ------------------------------------------------------------------
    # 2) COLLAB SCORE
    # ------------------------------------------------------------------
    try:
        info["Collab Score"] = card_element.find_element(
            By.CSS_SELECTOR, "[class*='hydrated']"
        ).text.strip()
    except Exception:
        pass

    # ------------------------------------------------------------------
    # 3) METRICS (Followers / Median Views / Engagement)
    # ------------------------------------------------------------------
    LABEL_MAP = {
        "Người theo dõi": "Followers",
        "Lượt xem trung vị": "Median Views",
        "Tương tác": "Engagement",
    }

    try:
        cols = card_element.find_elements(By.CSS_SELECTOR, "div.flex-1")
        for col in cols:
            # value
            try:
                value = col.find_element(
                    By.CSS_SELECTOR, "div.text-base.font-semibold"
                ).text.strip()
            except NoSuchElementException:
                continue
            except Exception:
                continue

            # label
            label = None
            try:
                label = col.find_element(By.CSS_SELECTOR, "span.titleLabel").text.strip()
            except NoSuchElementException:
                try:
                    label = col.find_element(
                        By.CSS_SELECTOR, "span[class*='titleLabel']"
                    ).text.strip()
                except Exception:
                    label = None
            except Exception:
                label = None

            if label in LABEL_MAP and value:
                info[LABEL_MAP[label]] = value
    except Exception:
        pass

    # ------------------------------------------------------------------
    # 4) START PRICE
    # ------------------------------------------------------------------
    try:
        price_xpath = (
            ".//span[contains(text(), 'Khởi điểm từ')]/.."
            "//div[contains(@class, 'text-base')]"
        )
        info["Start Price"] = card_element.find_element(By.XPATH, price_xpath).text.strip()
    except Exception:
        pass

    # ------------------------------------------------------------------
    # 5) TAGS MÀU (lọc tag màu, bỏ tag xám bg-gray-3)
    # ------------------------------------------------------------------
    tags = set()
    try:
        text_divs = card_element.find_elements(By.CSS_SELECTOR, ".truncated__text-single")
        for div in text_divs:
            text = div.text.strip()
            if not text or len(text) > 50:
                continue

            try:
                parent = div.find_element(
                    By.XPATH,
                    "./ancestor::div[contains(@class,'bg-') or contains(@class,'rounded')]"
                )
                parent_class = parent.get_attribute("class") or ""
                if "bg-gray-3" not in parent_class:
                    tags.add(text)
            except Exception:
                continue
    except Exception:
        pass

    info["Tags (Colored)"] = ", ".join(sorted(tags))
    return info


def get_virtual_container(driver, wait):
    """
    Lấy container virtual list. Đây là vùng scroll thật (overflow:auto).
    """
    try:
        return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.virtualCardResults")))
    except Exception:
        # fallback thô nếu selector đổi
        return driver.find_element(By.XPATH, "//div[@data-index]/..")


def scroll_container_down(driver, container, px=None):
    """
    Scroll đúng container bằng scrollTop (không click, không focus).
    """
    if px is None:
        px = random.randint(600, 1200)
    driver.execute_script("arguments[0].scrollTop += arguments[1];", container, px)


# =============================================================================
# 3. MAIN SCRIPT
# =============================================================================
print("--- ĐANG KHỞI ĐỘNG FIREFOX ---")
ser = Service(GECKO_PATH)
options = webdriver.firefox.options.Options()
options.binary_location = FIREFOX_BINARY_PATH
options.add_argument("-profile")
options.add_argument(MY_PROFILE_PATH)
options.set_preference("dom.webdriver.enabled", False)
options.set_preference("useAutomationExtension", False)

driver = webdriver.Firefox(options=options, service=ser)
wait = WebDriverWait(driver, 20)
action = ActionChains(driver)

try:
    # 1) Truy cập trang
    print(f"Truy cập: {TARGET_URL}")
    driver.get(TARGET_URL)
    driver.maximize_window()
    time.sleep(5)
    print("Tiêu đề trang:", driver.title)

    # ---------------------------------------------------------
    # (Optional) BƯỚC FILTER - đang comment theo code của bạn
    # ---------------------------------------------------------
    # Nếu cần bật lại filter thì giữ nguyên các block safe_click trước đó.

    # ---------------------------------------------------------
    # BƯỚC 2: CÀO DỮ LIỆU (DATA-INDEX SCROLLING)
    # ---------------------------------------------------------
    print(f"\n--- BẮT ĐẦU CÀO DỮ LIỆU (Mục tiêu: {TARGET_CREATOR_COUNT}) ---")

    collected_data = {}  # {index: data} để không trùng trong session
    last_highest_index = -1
    retry_scroll = 0

    container = get_virtual_container(driver, wait)

    while len(collected_data) < TARGET_CREATOR_COUNT:
        # A) Lấy thẻ hiển thị (virtualized list -> chỉ có các card visible)
        try:
            visible_cards = container.find_elements(By.CSS_SELECTOR, "div[data-index]")
        except StaleElementReferenceException:
            container = get_virtual_container(driver, wait)
            visible_cards = container.find_elements(By.CSS_SELECTOR, "div[data-index]")

        if not visible_cards:
            time.sleep(1)
            continue

        current_indices = []

        # B) Duyệt qua từng thẻ visible
        for card in visible_cards:
            try:
                idx_str = card.get_attribute("data-index")
                if not idx_str:
                    continue
                idx = int(idx_str)
                current_indices.append(idx)

                if idx in collected_data:
                    continue

                # đảm bảo card đang "active" trong viewport (giảm lỗi thiếu text)
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", card)
                    time.sleep(random.uniform(0.1, 0.3))
                except Exception:
                    pass

                details = extract_card_data(card)
                details["Index"] = idx
                collected_data[idx] = details

                print(
                    f" [OK] #{idx} {details['Name']} | "
                    f"Followers: {details['Followers']} | "
                    f"Median: {details['Median Views']} | "
                    f"Eng: {details['Engagement']} | "
                    f"Start: {details['Start Price']}"
                )

                if len(collected_data) >= TARGET_CREATOR_COUNT:
                    break

            except StaleElementReferenceException:
                continue
            except Exception:
                continue

        if len(collected_data) >= TARGET_CREATOR_COUNT:
            break

        # C) Logic cuộn để load card mới
        if not current_indices:
            break

        max_idx = max(current_indices)

        if max_idx == last_highest_index:
            retry_scroll += 1
            print(f"   ...Đang load thêm... ({retry_scroll})")

            # nếu kẹt lâu: scrollTop mạnh hơn
            if retry_scroll >= 4:
                scroll_container_down(driver, container, px=random.randint(800, 1400))
                time.sleep(random.uniform(1.2, 2.2))

            if retry_scroll > 10:
                print("⛔ Có thể đã hết danh sách hoặc bị giới hạn/rate limit.")
                break
        else:
            retry_scroll = 0
            last_highest_index = max_idx

            # scroll theo card cuối (vẫn hợp lý cho virtual list)
            try:
                last_card = container.find_element(By.CSS_SELECTOR, f"div[data-index='{max_idx}']")
                driver.execute_script("arguments[0].scrollIntoView({block:'start'});", last_card)
            except Exception:
                # fallback scrollTop
                scroll_container_down(driver, container)

        time.sleep(random.uniform(1.6, 3.0))

    # ---------------------------------------------------------
    # BƯỚC 3: XUẤT FILE
    # ---------------------------------------------------------
    print("\n--- KẾT THÚC CÀO ---")
    if collected_data:
        df = pd.DataFrame(list(collected_data.values())).sort_values(by="Index")

        # Sắp xếp cột cho đẹp, đồng bộ với extract_card_data
        cols = [
            "Index",
            "Name",
            "Collab Score",
            "Followers",
            "Median Views",
            "Engagement",
            "Start Price",
            "Tags (Colored)",
        ]
        # đảm bảo cột tồn tại
        cols = [c for c in cols if c in df.columns]
        df = df[cols]

        df.to_excel(OUTPUT_FILE, index=False)
        print(f"Đã lưu thành công {len(df)} dòng vào '{OUTPUT_FILE}'")
    else:
        print("Không thu thập được dữ liệu nào.")

except Exception as e:
    print(f"Lỗi Fatal: {e}")

finally:
    print("Hoàn tất.")
    # driver.quit()  # Bỏ comment nếu muốn tự động tắt trình duyệt
