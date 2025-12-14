import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

# =============================================================================
# 1. CẤU HÌNH (HÃY SỬA ĐƯỜNG DẪN CỦA BẠN TẠI ĐÂY)
# =============================================================================
MY_PROFILE_PATH = r"c:\Users\Admin\AppData\Roaming\Mozilla\Firefox\Profiles\3k9cekk1.default-release"
GECKO_PATH = r"C:\Users\Admin\Desktop\TANPHAT\Manguonmotrongkhoahocjdulieu\DOAN_MNM\tiktok\geckodriver.exe"
FIREFOX_BINARY_PATH = r"C:\Program Files\Mozilla Firefox\firefox.exe"

TARGET_CREATOR_COUNT = 20  # Số lượng Creator muốn cào

# =============================================================================
# 2. CÁC HÀM HỖ TRỢ (UTILS)
# =============================================================================

def safe_click(driver, xpath, retries=5):
    """Click an toàn chống lỗi StaleElement"""
    for i in range(retries):
        try:
            element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, xpath)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", element)
            return True
        except (StaleElementReferenceException, TimeoutException):
            time.sleep(1)
        except Exception as e:
            time.sleep(1)
    return False

def extract_card_data(card_element):
    """
    Trích xuất dữ liệu chi tiết từ 1 thẻ Creator
    """
    info = {
        "Name": "N/A",
        "Collab Score": "N/A",
        "Median Views": "N/A",
        "Engagement": "N/A",
        "Start Price": "N/A",
        "Tags (Colored)": ""
    }

    # 1. LẤY TÊN (Name) ổn
    try:
        # Thường nằm ở dòng đầu tiên hoặc class truncated__text-single đầu tiên
        name_elm = card_element.find_element(By.CSS_SELECTOR, ".truncated__text-single")
        info['Name'] = name_elm.text.strip()
    except:
        pass

    # 2. LẤY COLLAB SCORE (Điểm hợp tác - thẻ custom) tinh chỉnh
    try:
        # Tìm thẻ có class chứa 'hydrated' (thường là ks-tag)
        score_elm = card_element.find_element(By.CSS_SELECTOR, "[class*='hydrated']")
        info['Collab Score'] = score_elm.text.strip()
    except NoSuchElementException:
        pass

    # 3. LẤY MEDIAN VIEWS & ENGAGEMENT (Dựa vào Label text) không ổn
    def get_metric_by_label(label_text):
        try:
            # Tìm thẻ chứa Label -> Tìm cha (section) -> Tìm thẻ con chứa số liệu (font-semibold)
            xpath = f".//span[contains(text(), '{label_text}')]/ancestor::section//div[contains(@class, 'text-base font-semibold')]"
            return card_element.find_element(By.XPATH, xpath).text.strip()
        except NoSuchElementException:
            return "N/A"

    info['Median Views'] = get_metric_by_label("Lượt xem trung vị")
    info['Engagement'] = get_metric_by_label("Tương tác")

    # 4. LẤY GIÁ KHỞI ĐIỂM (Start From) ổn
    try:
        # Tìm Label 'Khởi điểm từ' -> Tìm cha -> Tìm số tiền
        price_xpath = ".//span[contains(text(), 'Khởi điểm từ')]/..//div[contains(@class, 'text-base')]"
        price_elm = card_element.find_element(By.XPATH, price_xpath)
        info['Start Price'] = price_elm.text.strip()
    except NoSuchElementException:
        pass

    # 5. LẤY TAGS MÀU (Ad Experience Tags) tinh chỉnh   
    tags_list = []
    try:
        # Tìm tất cả các thẻ text trong card
        all_text_divs = card_element.find_elements(By.CSS_SELECTOR, ".truncated__text-single")
        
        for div in all_text_divs:
            text = div.get_attribute("textContent").strip()
            if not text: continue
            
            # Tìm thẻ cha chứa background (để check màu)
            try:
                # Tìm thẻ cha gần nhất có class chứa 'rounded' hoặc 'bg-'
                parent = div.find_element(By.XPATH, "./ancestor::div[contains(@class, 'rounded') or contains(@class, 'bg-')]")
                parent_class = parent.get_attribute("class")
                div_class = div.get_attribute("class")
                
                # LOGIC LỌC:
                # - Bỏ qua tag màu xám (bg-gray-3)
                # - Tag phải có background (bg-...)
                # - Không phải là tên người (tên người thường không có bg-...)
                if "bg-gray-3" not in parent_class and ("bg-" in parent_class or "bg-" in div_class):
                    # Kiểm tra lại để chắc chắn không lấy nhầm tên người
                    if len(text) < 50: # Tag thường ngắn
                        tags_list.append(text)
            except:
                continue
    except Exception:
        pass
    
    # Lọc trùng và nối chuỗi
    info['Tags (Colored)'] = ", ".join(list(set(tags_list)))

    return info

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
    # 1. Truy cập trang
    target_url = "https://ads.tiktok.com/creative/forpartners/creator/explore?region=row"
    print(f"Truy cập: {target_url}")
    driver.get(target_url)
    driver.maximize_window()
    time.sleep(5)

    # ---------------------------------------------------------
    # BƯỚC 1: XỬ LÝ BỘ LỌC (QUỐC GIA & GIÁ) ổn
    # ---------------------------------------------------------
    print("\n--- CẤU HÌNH BỘ LỌC ---")
    
    # A. Chọn Quốc Gia: Việt Nam
    # Tìm nút mở menu Quốc gia (thường là nút filter đầu tiên)
    if safe_click(driver, "//div[contains(@class,'filter-trigger')][1]"):
        print("Mở menu Quốc gia...")
        time.sleep(2)
        
        # Chọn Việt Nam
        vn_xpath = "//div[contains(@class, 'truncated__text') and text()='Việt Nam']"
        if safe_click(driver, vn_xpath):
            print(" -> Tick 'Việt Nam'")
            time.sleep(1)
        else:
            print("[!] Không thấy tùy chọn Việt Nam")
    
    time.sleep(3) # Đợi reload

    # B. Chọn Giá: > 300 USD ổn
    # Tìm nút Giá (dựa trên class mới bạn cung cấp)
    price_trigger = "//div[contains(@class, 'filter-item-menu-label') and .//p[contains(text(), 'Giá')]]"
    fallback_trigger = "//p[text()='Giá']/ancestor::div[contains(@class, 'filter-item-menu-label')]"
    
    if safe_click(driver, price_trigger) or safe_click(driver, fallback_trigger):
        print("Mở menu Giá...")
        time.sleep(2)
        
        # Chọn > 300 USD
        price_opt = "//li[contains(@class, 'filter-form-select__item') and contains(text(), '> 300 USD')]"
        if safe_click(driver, price_opt):
            print(" -> Chọn '> 300 USD'")
            apply_xpath = "//button[contains(text(), 'Áp dụng')]"
            safe_click(driver, apply_xpath)
            print("Đã bấm Áp dụng.")
        else:
            # Dự phòng: chọn cái cuối cùng
            safe_click(driver, "//ul[contains(@class, 'filter-form-select')]/li[last()]")
            print(" -> Chọn mục giá cuối cùng (Fallback)")
            
        # Đóng menu (click ra ngoài)
        action.move_by_offset(200, 0).click().perform()
    else:
        print("[!] Không tìm thấy nút bộ lọc Giá")

    time.sleep(3)

    # ---------------------------------------------------------
    # BƯỚC 2: CÀO DỮ LIỆU (DATA-INDEX SCROLLING)
    # ---------------------------------------------------------
    print(f"\n--- BẮT ĐẦU CÀO DỮ LIỆU (Mục tiêu: {TARGET_CREATOR_COUNT}) ---")
    
    collected_data = {} # Dictionary {index: data} để không trùng
    last_highest_index = -1
    retry_scroll = 0
    
    # Tìm container chứa danh sách
    try:
        container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.virtualCardResults")))
    except:
        container = driver.find_element(By.XPATH, "//div[@data-index]/..")

    while len(collected_data) < TARGET_CREATOR_COUNT:
        # A. Lấy thẻ hiển thị
        visible_cards = container.find_elements(By.CSS_SELECTOR, "div[data-index]")
        
        if not visible_cards:
            time.sleep(1)
            continue
            
        current_indices = []
        
        # B. Duyệt qua từng thẻ
        for card in visible_cards:
            try:
                idx_str = card.get_attribute("data-index")
                if not idx_str: continue
                idx = int(idx_str)
                current_indices.append(idx)
                
                # Nếu index này chưa cào -> Xử lý
                if idx not in collected_data:
                    details = extract_card_data(card)
                    
                    # Gán Index vào để tracking
                    details['Index'] = idx
                    collected_data[idx] = details
                    
                    print(f" [OK] #{idx} {details['Name']} | Score: {details['Collab Score']} | Tags: {details['Tags (Colored)']}")
            except StaleElementReferenceException:
                continue
                
        # C. Logic Cuộn (Scroll)
        if not current_indices: break
        
        max_idx = max(current_indices)
        
        # Kiểm tra kẹt
        if max_idx == last_highest_index:
            retry_scroll += 1
            print(f"   ...Đang load thêm... ({retry_scroll})")
            if retry_scroll >= 5:
                # Cuộn cưỡng bức bằng pixel nếu bị kẹt lâu
                driver.execute_script("arguments[0].scrollTop += 800;", container)
                time.sleep(2)
            if retry_scroll > 10:
                print("Đã hết danh sách hoặc bị lỗi mạng.")
                break
        else:
            retry_scroll = 0
            last_highest_index = max_idx
            
            # Kỹ thuật cuộn: Đưa thẻ cuối cùng lên đầu để load thẻ mới
            try:
                last_card = container.find_element(By.CSS_SELECTOR, f"div[data-index='{max_idx}']")
                driver.execute_script("arguments[0].scrollIntoView({block: 'start', behavior: 'smooth'});", last_card)
            except:
                pass
        
        time.sleep(random.uniform(2, 3))

    # ---------------------------------------------------------
    # BƯỚC 3: XUẤT FILE
    # ---------------------------------------------------------
    print("\n--- KẾT THÚC CÀO ---")
    if collected_data:
        # Chuyển đổi dict -> list -> DataFrame
        data_list = list(collected_data.values())
        df = pd.DataFrame(data_list)
        
        # Sắp xếp theo index
        df = df.sort_values(by='Index')
        
        # Sắp xếp cột cho đẹp
        cols = ['Index', 'Name', 'Collab Score', 'Median Views', 'Engagement', 'Start Price', 'Tags (Colored)']
        df = df[cols]
        
        file_name = "tiktok_creators_final.xlsx"
        df.to_excel(file_name, index=False)
        print(f"Đã lưu thành công {len(df)} dòng vào '{file_name}'")
    else:
        print("Không thu thập được dữ liệu nào.")

except Exception as e:
    print(f"Lỗi Fatal: {e}")

finally:
    print("Hoàn tất.")
    # driver.quit() # Bỏ comment nếu muốn tự động tắt trình duyệt