import os
from typing import Optional
import google.generativeai as genai
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
# --- 1. KHỞI TẠO VÀ CẤU HÌNH ---
from sqlalchemy.orm import Session

import models
import database
# Tải API key từ file .env
api_key = os.getenv("AIzaSyCvOEzoZy4I5hJooz5bpayWI-nY9XLdo_k")
genai.configure(api_key=api_key)

# Khởi tạo ứng dụng FastAPI
app = FastAPI()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
    
# Cấu hình CORS (Cross-Origin Resource Sharing)
# RẤT QUAN TRỌNG: Cho phép frontend (chạy trên port khác) gọi được API này
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả các nguồn gốc (để phát triển)
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép tất cả các phương thức (POST, GET,...)
    allow_headers=["*"],  # Cho phép tất cả các header
)


# --- 2. ĐỊNH NGHĨA CẤU TRÚC DỮ LIỆU (PYDANTIC MODEL) ---
# Cấu trúc này PHẢI khớp với dữ liệu mà frontend gửi lên

class SurveyData(BaseModel):
    fullName: str
    anonymous: Optional[str] = None # Checkbox có thể không gửi giá trị
    className: str
    gender: str
    q1: int
    q2: int
    q3: int
    q4: int
    q5: int
    q6: int
    q7: int
    q8: int
    openEnded: Optional[str] = ""


# --- 3. KHỞI TẠO MÔ HÌNH GEMINI ---

generation_config = {
  "temperature": 0.7,
  "top_p": 1,
  "top_k": 1,
  "max_output_tokens": 2048,
}
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=generation_config
)


# --- 4. TẠO API ENDPOINT ---

@app.post("/submit-survey")
async def handle_survey(data: SurveyData, db: Session = Depends(get_db)):
    """
    Endpoint nhận dữ liệu khảo sát, xử lý và trả về phản hồi từ AI.
    """
        # --- BƯỚC 1: Chuẩn bị dữ liệu ---
    is_anonymous_bool = data.anonymous == 'on'
    full_name = "Ẩn danh" if is_anonymous_bool else data.fullName

        # --- BƯỚC 2: Tạo đối tượng để lưu ---
    db_response = models.SurveyResponse(
        fullName=full_name,
        is_anonymous=is_anonymous_bool,
        className=data.className,
        gender=data.gender,
        q1=data.q1, q2=data.q2, q3=data.q3, q4=data.q4,
        q5=data.q5, q6=data.q6, q7=data.q7, q8=data.q8,
        openEnded=data.openEnded
    )
        
    # --- BƯỚC 3: Gửi dữ liệu đến Supabase ---
    db.add(db_response)  # Thêm vào phiên làm việc
    db.commit()         # Xác nhận để lưu vĩnh viễn
    db.refresh(db_response) # Làm mới để lấy ID vừa tạo
        
    print(f"--- ✅ Dữ liệu đã được lưu vào Supabase với ID: {db_response.id} ---")
    # In dữ liệu nhận được để kiểm tra (bạn sẽ thấy trong terminal)
    print("--- Received Data ---")
    print(data.model_dump_json(indent=2))
    
    # --- Prompt Engineering: Tạo một prompt thông minh cho Gemini ---
    # Tổng hợp thông tin từ Likert scale để cung cấp ngữ cảnh cho AI
    context_summary = []
    if data.q3 >= 4: context_summary.append("thường cảm thấy lo lắng về kiểm tra")
    if data.q4 >= 4: context_summary.append("cảm thấy căng thẳng vì bài tập")
    if data.q5 <= 2: context_summary.append("khó khăn khi giao tiếp với bạn bè")
    if data.q8 >= 4: context_summary.append("hay nghi ngờ khả năng của bản thân")

    # Tạo prompt
    prompt = f"""
    Bạn là Emo, một chuyên gia tâm lý học đường ảo, một người bạn đồng hành ấm áp và đáng tin cậy của học sinh THPT.
    Một học sinh vừa chia sẻ cảm xúc của mình.
    
    Ngữ cảnh từ các câu trả lời trắc nghiệm: Học sinh này {', '.join(context_summary) if context_summary else "có cảm xúc khá ổn định"}.
    
    Chia sẻ thêm của học sinh: "{data.openEnded if data.openEnded else "Học sinh không chia sẻ gì thêm."}"
    
    Nhiệm vụ của bạn:
    1. Dựa vào CẢ NGỮ CẢNH và CHIA SẺ THÊM, hãy viết một phản hồi NGẮN GỌN (tối đa 3 câu), chân thành, tích cực và mang tính xây dựng.
    2. Giọng văn phải thật sự đồng cảm, không phán xét, như một người bạn lớn đang lắng nghe.
    3. Nếu học sinh chia sẻ điều tiêu cực, hãy công nhận cảm xúc đó và gợi ý một hướng suy nghĩ tích cực nhỏ.
    4. KHÔNG dùng các câu sáo rỗng như "Tôi hiểu cảm giác của bạn" hay "Tôi là một mô hình AI".
    5. Bắt đầu trực tiếp vào vấn đề. Tên của bạn là Emo.
    """
    
    try:
        response = model.generate_content(prompt)
        # Trả về phản hồi dạng JSON cho frontend
        return {"feedback": response.text}
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        # Ném một lỗi HTTP để frontend có thể xử lý
        raise HTTPException(status_code=500, detail="Có lỗi xảy ra khi tạo phản hồi từ AI.")

# (Thêm vào cuối file main.py)

from datetime import datetime, timedelta
from sqlalchemy import func

# --- PYDANTIC MODEL CHO DỮ LIỆU BIỂU ĐỒ ---
# Định nghĩa cấu trúc dữ liệu mà API sẽ trả về
class DailyEmotionData(BaseModel):
    date: str
    positive_avg: float
    negative_avg: float
    social_avg: float  # <--- THÊM DÒNG NÀY
    self_esteem_avg: float

# --- API ENDPOINT MỚI CHO DASHBOARD ---
@app.get("/dashboard-data", response_model=list[DailyEmotionData])
async def get_dashboard_data(
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db)
):
    """
    Endpoint này truy vấn CSDL, tổng hợp dữ liệu cảm xúc trung bình theo ngày
    và trả về cho frontend để vẽ biểu đồ.
    """
    # 1. Xử lý khoảng thời gian, sử dụng múi giờ UTC
    if end_date:
        # Chuyển ngày kết thúc thành cuối ngày (23:59:59) để bao gồm tất cả dữ liệu trong ngày
        end = datetime.fromisoformat(end_date).replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
    else:
        end = datetime.now(timezone.utc) # Lấy giờ hiện tại theo UTC

    if start_date:
        start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
    else:
        start = end - timedelta(days=30) # Mặc định là 30 ngày trước

    # 2. Truy vấn CSDL để tính toán và nhóm dữ liệu
    query_result = (
        db.query(
            func.date(models.SurveyResponse.created_at).label("date"),
            func.avg((models.SurveyResponse.q1 + models.SurveyResponse.q2) / 2).label("positive_avg"),
            func.avg((models.SurveyResponse.q3 + models.SurveyResponse.q4) / 2).label("negative_avg"),
            func.avg((models.SurveyResponse.q5 + models.SurveyResponse.q6) / 2).label("social_avg"),
            func.avg((models.SurveyResponse.q7 + (6 - models.SurveyResponse.q8)) / 2).label("self_esteem_avg")
        )
        # ✅ Đảm bảo việc lọc cũng diễn ra trong múi giờ đúng
        .filter(models.SurveyResponse.created_at.between(start, end))
        .group_by(func.date(models.SurveyResponse.created_at))
        .order_by(func.date(models.SurveyResponse.created_at).asc())
        .all()
    )

    # 3. Định dạng lại dữ liệu trước khi trả về
    return [
        DailyEmotionData(
            date=row.date.isoformat(),
            positive_avg=round(row.positive_avg, 2) if row.positive_avg else 0,
            negative_avg=round(row.negative_avg, 2) if row.negative_avg else 0,
            social_avg=round(row.social_avg, 2) if row.social_avg else 0,
            self_esteem_avg=round(row.self_esteem_avg, 2) if row.self_esteem_avg else 0
        ) for row in query_result
    ]