import os
import re
from src.preprocessing import extract_text_from_binary

# Bảng quy chuẩn mã số của Phụ lục Nghị định 30 thành Thẻ biến số (Tags)
TAG_MAP = {
    "1": "[TÊN CƠ QUAN CHỦ QUẢN]",
    "2": "[TÊN CƠ QUAN BAN HÀNH]",
    "3": "[CHỮ VIẾT TẮT TÊN CƠ QUAN]",
    "4": "[ĐỊA DANH]",
    "5": "[TRÍCH YẾU NỘI DUNG]",
    "6": "[NỘI DUNG VÀ THẨM QUYỀN]",
    "7": "[CĂN CỨ VÀ ĐƠN VỊ NHẬN]",
    "8": "[CHÚ THÍCH THÊM]",
    "9": "[SỐ BẢN LƯU]",
    "10": "[NGƯỜI SOẠN THẢO]"
}

def clean_decree_template(text: str) -> str:
    """Hàm dọn dẹp văn bản thô của Nghị định 30 thành Template cho AI"""
    # 1. Cắt bỏ hoàn toàn phần "Ghi chú:" ở cuối trang
    if "Ghi chú:" in text:
        text = text.split("Ghi chú:")[0]

    # 2. Thay thế các con số nằm giữa dấu chấm (vd: ...3..., ..4..) thành Thẻ
    def replace_numbered_dots(match):
        num = match.group(1)
        return f" {TAG_MAP.get(num, '[...]')} "
    
    text = re.sub(r'\.\.+(\d+)\.\.+', replace_numbered_dots, text)
    
    # 3. Thay thế các con số đứng lẻ loi ở lề
    for num, tag in TAG_MAP.items():
        text = re.sub(rf'(?<!\d){num}(?!\d)', f'{tag}', text)
        
    # 4. Thay thế các đoạn chấm lửng dài còn lại thành chỗ trống
    text = re.sub(r'\.\.\.\.+', '[Nội dung chi tiết...]', text)
    
    # 5. Dọn dẹp khoảng trắng
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

def process_templates(input_dir="data/raw_templates", output_dir="data/templates"):
    os.makedirs(output_dir, exist_ok=True)
    
    for filename in os.listdir(input_dir):
        if filename.endswith(".pdf"):
            input_path = os.path.join(input_dir, filename)
            
            with open(input_path, "rb") as f:
                raw_bytes = f.read()
            
            raw_text = extract_text_from_binary(raw_bytes, filename)
            cleaned_text = clean_decree_template(raw_text)
            
            output_filename = filename.replace(".pdf", ".txt")
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(cleaned_text)
                
            print(f"✅ Đã chuẩn hóa xong: {output_filename}")

if __name__ == "__main__":
    process_templates()