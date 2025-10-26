import os
from groq import Groq
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
# --- 1. KHỞI TẠO VÀ CẤU HÌNH ---
from sqlalchemy.orm import Session

import models
import database
# Tải API key từ file .env
# Khởi tạo client Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
# Chọn model của Groq (llama3-8b là model nhanh nhất)
GROQ_MODEL = "qwen/qwen3-32b"

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
    if data.q1 == 1: context_summary.append("cảm thấy căng thẳng khi tham gia các tiết học trên lớp.")
    if data.q1 == 2: context_summary.append("cảm thấy buồn khi tham gia các tiết học trên lớp.")
    if data.q1 == 3: context_summary.append("cảm thấy bình thường khi tham gia các tiết học trên lớp.")
    if data.q1 == 4: context_summary.append("cảm thấy vui vẻ khi tham gia các tiết học trên lớp.")
    if data.q1 == 5: context_summary.append("cảm thấy hào hứng khi tham gia các tiết học trên lớp.")
        
    if data.q2 == 1: context_summary.append("cảm thấy căng thẳng khi đến trường.")
    if data.q2 == 2: context_summary.append("cảm thấy lạc lõng khi đến trường.")
    if data.q2 == 3: context_summary.append("cảm thấy bình thường khi đến trường.")
    if data.q2 == 4: context_summary.append("cảm thấy vui vẻ khi đến trường.")
    if data.q2 == 5: context_summary.append("cảm thấy hào hứng khi đến trường.")

    if data.q3 == 1: context_summary.append("cảm thấy Sợ hãi khi chứng kiến bạo lực học đường.")
    if data.q3 == 2: context_summary.append("cảm thấy buồn khi chứng kiến bạo lực học đường.")
    if data.q3 == 3: context_summary.append("cảm thấy bình thường khi chứng kiến bạo lực học đường.")
    if data.q3 == 4: context_summary.append("cảm thấy vui vẻ khi chứng kiến bạo lực học đường.")
    if data.q3 == 5: context_summary.append("cảm thấy hứng thú khi chứng kiến bạo lực học đường.")

    if data.q4 == 1: context_summary.append("cảm thấy Căng thẳng khi giao tiếp với bạn bè trong lớp.")
    if data.q4 == 2: context_summary.append("cảm thấy Sợ hãi khi giao tiếp với bạn bè trong lớp.")
    if data.q4 == 3: context_summary.append("cảm thấy bình thường khi giao tiếp với bạn bè trong lớp.")
    if data.q4 == 4: context_summary.append("cảm thấy vui vẻ khi giao tiếp với bạn bè trong lớp.")
    if data.q4 == 5: context_summary.append("cảm thấy Hào hứng khi giao tiếp với bạn bè trong lớp.")

    if data.q5 == 1: context_summary.append("cảm thấy Nhàm chán khi có ứng dụng ghi lại cảm xúc hằng ngày.")
    if data.q5 == 2: context_summary.append("cảm thấy Vô dụng khi có ứng dụng ghi lại cảm xúc hằng ngày.")
    if data.q5 == 3: context_summary.append("cảm thấy không quan tâm khi có ứng dụng ghi lại cảm xúc hằng ngày.")
    if data.q5 == 4: context_summary.append("cảm thấy phù hợp khi có ứng dụng ghi lại cảm xúc hằng ngày.")
    if data.q5 == 5: context_summary.append("cảm thấy hào hứng khi có ứng dụng ghi lại cảm xúc hằng ngày.")  

    if data.q6 == 1: context_summary.append("cảm thấy căng thẳng khi chia sẻ cảm xúc của mình đối với người khác.")
    if data.q6 == 2: context_summary.append("cảm thấy Lo lắng khi chia sẻ cảm xúc của mình đối với người khác.")
    if data.q6 == 3: context_summary.append("cảm thấy bình thường khi chia sẻ cảm xúc của mình đối với người khác.")
    if data.q6 == 4: context_summary.append("cảm thấy An toàn khi chia sẻ cảm xúc của mình đối với người khác.")
    if data.q6 == 5: context_summary.append("cảm thấy Vui vẻ khi chia sẻ cảm xúc của mình đối với người khác.")  

    if data.q7 == 1: context_summary.append("cảm thấy Chán ghét với bản thân mình.")
    if data.q7 == 2: context_summary.append("cảm thấy Thất vọng với bản thân mình.")
    if data.q7 == 3: context_summary.append("cảm thấy bình thường với bản thân mình.")
    if data.q7 == 4: context_summary.append("cảm thấy vui vẻ với bản thân mình.")
    if data.q7 == 5: context_summary.append("cảm thấy Tự hào với bản thân mình.")  

    if data.q2 == 1: context_summary.append("cảm thấy Tự ti khả năng của bản thân..")
    if data.q2 == 2: context_summary.append("cảm thấy Thất vọng khả năng của bản thân..")
    if data.q2 == 3: context_summary.append("cảm thấy bình thường khả năng của bản thân..")
    if data.q2 == 4: context_summary.append("cảm thấy Hài lòng khả năng của bản thân..")
    if data.q2 == 5: context_summary.append("cảm thấy Tự tin khả năng của bản thân..")  


    # Tạo prompt
    prompt = f"""
    Bạn là Emo, một giáo viên rất yêu thương HS, một chuyên gia tâm lý học đường ảo của học sinh THPT.
    Lắng nghe và đưa ra lời khuyên nhẹ nhàng, truyền cảm hứng cho ngày hôm sau. Một học sinh vừa chia sẻ cảm xúc của mình như sau:
    Tên của HS là {full_name}, giới tính là {data.gender}.
    Hãy phản hồi theo cấu trúc chỉ với 3 đoạn trừ lời chào sau:
    - Lời chào thân mật (gọi tên học sinh theo cách dễ thương, gần gũi, ví dụ “Chào Minh nè 💛”).
    - Đoạn tâm sự ngắn gọn thể hiện sự thấu hiểu và đồng cảm với tâm sự của học sinh (dùng ngôn ngữ nhẹ nhàng, không phán xét).
    - Đưa ra lời khuyên tích cực, ngắn gọn – giúp học sinh biết nên làm gì để có một ngày vui hơn hoặc nhẹ lòng hơn vào ngày hôm sau (gợi ý hành động cụ thể, như nghe nhạc, viết nhật ký, nói chuyện với bạn bè, đi dạo, tự thưởng món yêu thích, v.v.).
    - Kết thúc bằng một thông điệp ngắn gọn khích lệ (ví dụ: “Ngày mai chắc chắn sẽ tốt hơn đó 🌈” hoặc “Bạn đang làm rất tốt rồi, đừng quên mỉm cười nhé 💪”).
    Giọng văn nên:
    - Ấm áp, chân thành, phù hợp với học sinh THPT
    - Không phán xét
    - Không dùng từ chuyên môn tâm lý học quá nhiều
    - Có thể thêm emoji nhẹ nhàng để tăng cảm xúc tích cực
    Ngữ cảnh từ câu trả lời Học sinh này {', '.join(context_summary) if context_summary else "có cảm xúc khá ổn định"}.
    Chia sẻ thêm của học sinh: "{data.openEnded if data.openEnded else "Học sinh không chia sẻ gì thêm."}"
    """
    
    # THÊM KHỐI NÀY VÀO
    try:
        # Groq sử dụng định dạng chat giống OpenAI
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt, # Pro
                }
            ],
            model=GROQ_MODEL,
            temperature=0.7,
            max_completion_tokens=4096,
            top_p=1,
            reasoning_effort="default",
            stream=True,
            stop=None
        )
        
        feedback_text = chat_completion.choices[0].message.content
        
        if not feedback_text:
             feedback_text = "Emo đang suy nghĩ thêm một chút, bạn hãy thử lại nhé!"
        
        return {"feedback": feedback_text}
    
    except Exception as e:
        print(f"!!! Error calling Groq API: {e}")
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












