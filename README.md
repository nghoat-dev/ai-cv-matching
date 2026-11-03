# AI CV-Job Matching System (Hệ thống Khớp nối CV và Mô tả Công việc bằng AI)

> **Hệ thống tuyển dụng thông minh ứng dụng Machine Learning (Scikit-Learn) và Large Language Model (Gemini / Rule Guardrails) để tự động đánh giá mức độ phù hợp giữa hồ sơ ứng viên (CV PDF) và bản mô tả công việc (Job Description - JD).**

---

## 1. Giới thiệu Tổng quan Dự án

Hệ thống **AI CV-Job Matching** giải quyết bài toán cốt lõi trong sàng lọc ứng viên tự động:
- **Tách xuất thực thể thông minh (US-14, US-16):** Đọc trực tiếp file PDF đa trang bằng `PyMuPDF (fitz)`, kiểm tra tính toàn vẹn (magic bytes `%PDF-`), phân loại kỹ năng (Skills Taxonomy) và kinh nghiệm làm việc.
- **Mô hình Máy học nâng cao (US-17, US-18, US-24):** Trích xuất đặc trưng TF-IDF song hành (20.000 chiều) kết hợp độ tương đồng Cosine, tỉ lệ trùng lặp từ khóa (Token Overlap) và độ dài văn bản. Phân loại 3 mức độ: **Good Fit**, **Potential Fit**, **No Fit**.
- **Giải thích quyết định tự nhiên (US-19):** Tích hợp Gemini LLM (có cơ chế Fallback tự động khi không có API Key) để phân tích điểm mạnh, điểm yếu và đưa ra khuyến nghị tuyển dụng.
- **Bảng điều khiển trực quan (US-22, US-23, US-29):** Giao diện Web SPA tích hợp sẵn (không phụ thuộc Node.js), có đồng hồ đo điểm số động (SVG Gauge), nhãn kỹ năng màu xanh/đỏ, lịch sử tra cứu và biểu đồ thống kê thời gian thực.
- **Xếp hạng & So sánh đa ứng viên (US-26, US-27):** So sánh cùng lúc nhiều CV trên 1 bản mô tả công việc, xếp hạng từ cao xuống thấp và xuất báo cáo CSV/JSON.

---

## 2. Kết quả 3 Sprint (Sprint 1 -> Sprint 2 -> Sprint 3)

| Chỉ số / Tiêu chí | Sprint 1 (Baseline) | Sprint 2 (Enhanced) | Sprint 3 (Production) |
|---|---|---|---|
| **Mô hình ML** | Logistic Regression (C=1.0) | Tuned Logistic Regression (C=2.8) | Calibrated Hybrid ML Artifact v2 |
| **Độ chính xác (Accuracy)** | 77.15% | **82.29%** (+5.14%) | **82.29%** |
| **Macro F1-Score** | 67.89% | **71.04%** (+3.15%) | **71.04%** |
| **Weighted F1-Score** | 78.77% | **82.35%** (+3.58%) | **82.35%** |
| **Good Fit Precision** | 48.25% | **60.00%** (+11.75%) | **60.00%** |
| **Thời gian suy luận (Latency)** | ~45 ms / cặp CV-JD | ~48 ms / cặp CV-JD | **< 50 ms** |
| **Endpoints REST API** | 3 endpoints | 6 endpoints | **10 production endpoints** |
| **Giao diện người dùng** | Swagger UI thô | Form cơ bản | **Web SPA hiện đại + Lịch sử + Thống kê** |
| **Đóng gói Docker** | Chưa có | Chưa có | **Dockerfile + docker-compose.yml** |
| **Bộ kiểm thử tự động** | Đơn lẻ | Đơn lẻ | **Master Test Suite 100% Pass** |

---

## 3. Kiến trúc Hệ thống

```
d:\AI_CV_Matching\
├── backend\
│   ├── app\
│   │   ├── main.py              # FastAPI Router (10 Endpoints, CORS, Error Handlers)
│   │   ├── database.py          # SQLite engine & SQLAlchemy session
│   │   ├── models.py            # ORM Tables: cv_records, jd_records, matching_results
│   │   ├── schemas.py           # Pydantic Schemas (MatchingResponse, etc.)
│   │   ├── web_ui.py            # Giao diện Web SPA tích hợp sẵn (HTML5/CSS3/JS)
│   │   └── services\
│   │       ├── cv_extractor.py  # PyMuPDF + Regex Entity Extraction (Tên, Email, Kỹ năng)
│   │       └── llm_service.py   # LLM Wrapper (Gemini + Heuristic Fallback)
│   ├── tests\
│   │   ├── test_api_direct.py   # Bộ test toàn diện 12 API endpoints
│   │   └── test_api_sprint2_3.py
│   ├── seed_demo_data.py        # Script tạo dữ liệu mẫu phong phú
│   └── verify_env.py            # Kiểm tra môi trường & thư viện
├── ml_pipeline\
│   ├── clean_data.py            # Data Cleaning & Deduplication
│   ├── preprocessing.py         # Text Normalization & Bảo toàn Tech Token
│   ├── feature_extraction.py    # Shared TF-IDF + Pairwise Cosine/Overlap
│   ├── train_baseline.py        # Huấn luyện mô hình Baseline v1
│   ├── train_advanced.py        # Huấn luyện mô hình Nâng cao v2 (US-17)
│   ├── evaluate_advanced.py     # Đánh giá mô hình v2 trên tập kiểm thử độc lập
│   ├── scoring.py               # Công thức tính điểm tương thích 0-100 (US-18)
│   └── tests\test_pipeline_unit.py
├── frontend\                    # Mã nguồn React (App.jsx, MatchForm, ResultCard, v.v.)
│   └── src\
├── models\
│   ├── baseline_pipeline_v1.joblib # Model Sprint 1
│   └── advanced_pipeline_v2.joblib # Model Sprint 2 & 3
├── data\
│   └── processed\train.csv, test.csv
├── Documents\
│   ├── Sample_CV_Python_Developer.pdf  # CV mẫu Python Developer (Dùng để demo)
│   └── Sample_CV_Accountant.pdf        # CV mẫu Kế toán (Dùng để demo)
├── reports\
│   ├── sprint1_baseline_report.md
│   ├── sprint2_model_report.md
│   └── sprint3_final_report.md
├── run_all_tests.py             # Bộ chạy kiểm thử tổng hợp (Master Test Suite)
├── Dockerfile                   # Dockerfile triển khai container
├── docker-compose.yml           # Triển khai 1-lệnh bằng Docker Compose
└── requirements.txt
```

---

## 4. Hướng dẫn Khởi chạy & Demo Chi tiết cho Giảng viên

### Cách 1: Chạy trực tiếp trên máy (Khuyên dùng khi demo)

#### Bước 1: Khởi động Server Backend
Mở PowerShell hoặc Terminal tại thư mục `d:\AI_CV_Matching`:
```powershell
d:\anacoda\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
*(Nếu dùng Python chuẩn máy cá nhân: `python -m uvicorn backend.app.main:app --port 8000 --reload`)*

#### Bước 2: Mở Giao diện Web trên trình duyệt
Truy cập địa chỉ:
👉 **[http://localhost:8000/](http://localhost:8000/)** hoặc **[http://localhost:8000/app](http://localhost:8000/app)**

---

### Hướng dẫn 3 Kịch bản Demo ấn tượng cho Giảng viên:

#### 🎯 Kịch bản 1: Demo Khớp nối Ứng viên Chuẩn ("Good Fit")
1. Kéo thả hoặc chọn file CV PDF từ thư mục `Documents/Sample_CV_Python_Developer.pdf`.
2. Dán đoạn mô tả công việc (Job Description), ví dụ:
   > "Tuyển Senior Python Backend Developer. Yêu cầu: 3+ năm kinh nghiệm với Python, FastAPI, Docker, PostgreSQL, Redis, CI/CD, Git."
3. Bấm nút **"🔍 Analyze Compatibility"**.
4. **Kết quả hiển thị trong < 0.5s:**
   - Điểm số: **~90 – 100 điểm** (Vạch đồng hồ màu xanh lá cây).
   - Nhãn: **✅ Good Fit**.
   - Matched Skills: `Python`, `FastAPI`, `PostgreSQL`, `Docker`, `Git`, v.v.
   - Giải thích AI: Nêu rõ kinh nghiệm phù hợp với vị trí backend.

#### 🎯 Kịch bản 2: Demo Phát hiện Ứng viên Không Phù hợp ("No Fit")
1. Chọn file CV kế toán từ thư mục `Documents/Sample_CV_Accountant.pdf` (Giữ nguyên JD Senior Python).
2. Bấm nút **"🔍 Analyze Compatibility"**.
3. **Kết quả hiển thị ngay:**
   - Điểm số: **~4 – 6 / 100 điểm** (Vạch đồng hồ màu đỏ).
   - Nhãn: **❌ No Fit**.
   - Missing Skills: Cảnh báo thiếu toàn bộ kỹ năng lập trình bắt buộc.
   - Giải thích AI: Phân tích rõ sự không tương thích giữa ngành Tài chính/Kế toán và Kỹ sư phần mềm.

#### 🎯 Kịch bản 3: Tra cứu Lịch sử & Thống kê Thời gian thực
1. Bấm tab **"📋 History"**: Xem danh sách toàn bộ các lượt sàng lọc vừa thực hiện, có phân loại màu sắc, ngày giờ và nút lọc theo nhãn.
2. Bấm tab **"📊 Statistics"**: Xem biểu đồ tỷ lệ phân bố Good Fit, Potential Fit, No Fit và điểm số trung bình toàn hệ thống.

---

## 5. Danh sách Endpoints REST API (Swagger)

Tài liệu Swagger tương tác trực tiếp tại: 👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

| Phương thức | Đường dẫn API | Mô tả tính năng |
|---|---|---|
| `POST` | `/api/v1/match` | Khớp nối CV PDF và JD bằng ML Model v2 + LLM |
| `POST` | `/api/v1/extract` | Tách xuất thực thể ứng viên (Tên, Email, Kỹ năng, Học vấn) |
| `POST` | `/api/v1/compare` | So sánh và xếp hạng nhiều CV trên cùng 1 JD (Leaderboard) |
| `GET` | `/api/v1/history` | Lấy lịch sử khớp nối (hỗ trợ tìm kiếm, lọc theo nhãn, phân trang) |
| `DELETE`| `/api/v1/history/{id}` | Xóa một bản ghi trong lịch sử |
| `GET` | `/api/v1/history/export` | Xuất toàn bộ dữ liệu lịch sử ra file CSV hoặc JSON |
| `GET` | `/api/v1/stats` | Thống kê tổng hợp (tổng CV, điểm TB, tỷ lệ phân bố) |
| `GET` | `/health` | Kiểm tra trạng thái hoạt động (Liveness probe) |
| `GET` | `/api/v1/info` | Thông tin siêu dữ liệu API & Mô hình đang tải |
| `GET` | `/app` hoặc `/` | Giao diện Web SPA tích hợp |

---

## 6. Chạy Kiểm thử Toàn diện (Master Test Suite)

Để kiểm tra 100% tính đúng đắn của toàn bộ dự án từ Sprint 1 đến Sprint 3:

```powershell
d:\anacoda\python.exe run_all_tests.py
```

Kết quả:
```
=================================================================
  ALL TEST SUITES PASSED (100% SUCCESS RATE) - SYSTEM READY FOR DEMO!
=================================================================
```

---

## 7. Triển khai bằng Docker (Production Ready)

Hệ thống đã sẵn sàng đóng gói container:

```bash
# Khởi động dịch vụ container
docker compose up --build -d

# Kiểm tra trạng thái
docker compose ps

# Xem log
docker compose logs -f
```
Sau đó mở trình duyệt tại `http://localhost:8000` để sử dụng.
