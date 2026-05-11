import json
from pathlib import Path

# Vẫn là 29 loại chuẩn NĐ30
ND30_VALID_DOC_TYPES = {
    "Nghị quyết", "Quyết định", "Chỉ thị", "Quy chế", "Quy định", "Hướng dẫn",
    "Thông cáo", "Thông báo", "Báo cáo", "Biên bản", "Tờ trình",
    "Chương trình", "Kế hoạch", "Phương án", "Đề án", "Dự án",
    "Công văn", "Công điện", "Bản ghi nhớ", "Bản thỏa thuận", "Hợp đồng",
    "Giấy ủy quyền", "Giấy mời", "Giấy giới thiệu", "Giấy nghỉ phép",
    "Phiếu gửi", "Phiếu chuyển", "Phiếu báo", "Thư công"
}

def audit_json_file(filepath: str):
    print(f"🔍 Bắt đầu kiểm toán file: {filepath}...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        error_count = 0
        for item in data:
            doc_id = item.get("id", "Unknown-ID")
            doc_type = item.get("doc_type", "")
            
            # Kiểm tra lỗi sai quy chuẩn
            if doc_type not in ND30_VALID_DOC_TYPES:
                error_count += 1
                print(f"  ❌ Lỗi [ID: {doc_id}]: 'doc_type' là '{doc_type}' -> KHÔNG NẰM TRONG 29 LOẠI CỦA NĐ 30!")
                
        if error_count == 0:
            print(f"  ✅ CHUẨN: 100% dữ liệu đạt chuẩn Nghị định 30.\n")
        else:
            print(f"  ⚠️ CẢNH BÁO: Phát hiện {error_count} văn bản sai chuẩn pháp lý!\n")
            
    except Exception as e:
        print(f" Lỗi đọc file: {e}")

if __name__ == "__main__":
    # Test ngay với 2 file JSON hiện tại của nhóm
    files_to_check = ["admin_docs.json", "sprint2_sample_docs.json"]
    for file in files_to_check:
        if Path(file).exists():
            audit_json_file(file)
        else:
            print(f"Không tìm thấy file: {file}")