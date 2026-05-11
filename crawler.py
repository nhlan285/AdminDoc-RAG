import time
import json
import requests
import io
from docx import Document as DocxDocument
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==========================================
# 1. CẤU HÌNH TRÌNH DUYỆT & ĐĂNG NHẬP
# ==========================================
def setup_driver():
    chrome_options = Options()
    # Bỏ comment dòng dưới nếu muốn chạy ẩn (không hiện cửa sổ Chrome)
    # chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def login_thuvienphapluat(driver, username, password):
    """Hàm tự động điền User/Pass để vượt rào đăng nhập TVPL"""
    print("🔐 Đang tiến hành đăng nhập Thư Viện Pháp Luật...")
    driver.get("https://thuvienphapluat.vn/")
    time.sleep(2)
    
    try:
        # Nhấn nút đăng nhập góc phải (Cần F12 kiểm tra lại ID/Class nếu web đổi)
        login_btn = driver.find_element(By.ID, "btn-login-home")
        login_btn.click()
        time.sleep(1)
        
        # Điền form
        driver.find_element(By.ID, "customerName").send_keys(username)
        driver.find_element(By.ID, "customerPass").send_keys(password)
        driver.find_element(By.ID, "btnLogin").click()
        
        print("✅ Đăng nhập thành công! Chờ 3s để lưu Session...")
        time.sleep(3)
    except Exception as e:
        print("⚠️ Không thể đăng nhập tự động, có thể web đã đổi giao diện. Vui lòng check lại CSS Selector.")

# ==========================================
# 2. XỬ LÝ KHUÔN CHUẨN (TẢI FILE WORD)
# ==========================================
def extract_text_from_docx_url(docx_url):
    """Tải file .docx từ URL và bóc tách chữ bên trong"""
    try:
        response = requests.get(docx_url)
        response.raise_for_status()
        doc = DocxDocument(io.BytesIO(response.content))
        
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text.strip())
        return "\n".join(full_text)
    except Exception as e:
        print(f"❌ Lỗi tải/đọc file Word: {docx_url} - {e}")
        return ""

# ==========================================
# 3. CÀO MẪU VĂN BẢN TRÊN BÀI VIẾT TỔNG HỢP
# ==========================================
def scrape_template_article(driver, url, doc_type, base_tags):
    """Vào thẳng 1 bài viết, tìm cái bảng/khung chứa biểu mẫu để cào"""
    print(f"🔎 Đang cào bài viết: {url}")
    driver.get(url)
    time.sleep(3) # Chờ load
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    documents = []
    
    # Lấy Tiêu đề bài viết
    article_title = soup.find('h1')
    title_text = article_title.get_text(strip=True) if article_title else "Mẫu văn bản không tên"

    # CHIẾN THUẬT 1: Tìm link tải file Word (.doc, .docx) trong bài
    docx_links = soup.find_all('a', href=lambda href: href and (".doc" in href or ".docx" in href))
    for i, link in enumerate(docx_links):
        file_url = link['href']
        if not file_url.startswith("http"):
            file_url = "https://luatvietnam.vn" + file_url # Thay domain tương ứng
            
        print(f"   📥 Phát hiện file Word: {file_url}")
        doc_content = extract_text_from_docx_url(file_url)
        
        if doc_content:
            documents.append({
                "id": f"DOCX-{int(time.time())}-{i}",
                "title": f"{title_text} (Bản Word chuẩn)",
                "doc_type": doc_type,
                "source": url,
                "tags": base_tags + ["khuôn chuẩn", "file word"],
                "content": doc_content
            })

    # CHIẾN THUẬT 2: Nếu không có file Word, cào text trong khung HTML
    if not documents: 
        print("   📝 Không thấy file Word, tiến hành cào Text trong biểu mẫu HTML...")
        
        # 1. Tìm ĐÚNG khung chứa BÀI VIẾT CHÍNH (Bỏ qua menu, sidebar trang web)
        # Các class đặc trưng của trang Luật Việt Nam và Thư Viện Pháp Luật
        content_area = soup.find('div', class_='article__body') or soup.find('div', class_='post-content') or soup.find('div', id='article-content') or soup.find('article')
        
        if content_area:
            # 2. XÓA SẠCH RÁC HTML trước khi lấy chữ (Xóa quảng cáo, bài liên quan, form đánh giá)
            trash_classes = ['related-news', 'box-danh-gia', 'box-tag', 'author-info', 'toc', 'hotline-box']
            for trash in content_area.find_all(['div', 'ul', 'section'], class_=trash_classes):
                trash.decompose() # Bứng gốc phần tử HTML này đi
            
            # 3. Lấy text và dọn dẹp các dòng trống
            raw_text = content_area.get_text(separator="\n", strip=True)
            
            # 4. Bộ lọc Text (Cắt bỏ phần chân trang dính chữ "1900" hoặc "Luật sư")
            clean_lines = []
            for line in raw_text.split('\n'):
                # Nếu đụng phải chân trang quảng cáo thì dừng lấy text ngay lập tức
                if "1900.6192" in line or "1900 6192" in line or "Luật sư tư vấn" in line or "Đánh giá bài viết" in line:
                    break
                # Chỉ lấy những dòng có ý nghĩa
                if len(line.strip()) > 0 and line.strip() not in [">>", "X"]:
                    clean_lines.append(line.strip())
            
            final_text = "\n".join(clean_lines).strip()
            
            # Chỉ lưu nếu bài viết đủ dài (tránh cào nhầm trang rỗng)
            if len(final_text) > 150: 
                documents.append({
                    "id": f"HTML-{int(time.time())}",
                    "title": title_text,
                    "doc_type": doc_type,
                    "source": url,
                    "tags": base_tags + ["biểu mẫu html"],
                    "content": final_text
                })
            else:
                print("   ⚠️ Nội dung quá ngắn, nghi ngờ cào lỗi, đã bỏ qua!")

    return documents

# ==========================================
# 4. HÀM CHÍNH (MAIN)
# ==========================================
if __name__ == "__main__":
    # --- DANH SÁCH URL CẦN CÀO ---
    # Em thêm các link bài viết chứa biểu mẫu trên mạng vào đây
    target_urls = [
        # Link thật Công văn giải trình
        {
            "url": "https://luatvietnam.vn/hanh-chinh/mau-cong-van-giai-trinh-570-33158-article.html", 
            "type": "Công văn", 
            "tags": ["giải trình", "báo cáo", "trình bày nguyên nhân"]
        },
        # Link thật Tờ trình mua sắm thiết bị
        {
            "url": "https://luatvietnam.vn/hanh-chinh/to-trinh-la-gi-mau-to-trinh-570-35619-article.html", 
            "type": "Tờ trình", 
            "tags": ["mua sắm", "thiết bị", "xin kinh phí", "đề nghị"]
        },
        # Link thật Quyết định thành lập ban chỉ đạo
        {
            "url": "https://luatvietnam.vn/hanh-chinh/mau-quyet-dinh-thanh-lap-ban-chi-dao-570-90924-article.html",
            "type": "Quyết định",
            "tags": ["thành lập ban", "chỉ đạo dự án", "bổ nhiệm"]
        }
    ]
    
    driver = setup_driver()
    
    # BƯỚC 1: Đăng nhập (Nếu có tài khoản TVPL thì điền vào, không thì comment dòng dưới lại)
    # login_thuvienphapluat(driver, "user_cua_tinh", "pass_cua_tinh")
    
    all_extracted_docs = []
    
    # BƯỚC 2: Duyệt qua từng Link để cào
    for item in target_urls:
        docs = scrape_template_article(driver, item["url"], item["type"], item["tags"])
        all_extracted_docs.extend(docs)
        
    driver.quit()
    
    # BƯỚC 3: Lưu thành file JSON để nạp vào Vector DB
    output_filename = "sprint3_khuon_mau_hanh_chinh.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(all_extracted_docs, f, ensure_ascii=False, indent=2)
        
    print(f"\n🎉 HOÀN TẤT! Đã cào và lưu {len(all_extracted_docs)} mẫu văn bản chuẩn vào file '{output_filename}'")
    print("💡 Mở file JSON ra kiểm tra, đưa cho Huy chạy qua preprocessing.py rồi nạp cho thuật toán của Lân nhé!")