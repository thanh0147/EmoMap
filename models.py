# file: models.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from database import Base

# Định nghĩa model (bảng) để lưu trữ các phản hồi khảo sát
class SurveyResponse(Base):
    __tablename__ = "survey_responses"

    id = Column(Integer, primary_key=True, index=True)
    fullName = Column(String)
    is_anonymous = Column(Boolean, default=False)
    className = Column(String)
    gender = Column(String)
    
    q1 = Column(Integer)
    q2 = Column(Integer)
    q3 = Column(Integer)
    q4 = Column(Integer)
    q5 = Column(Integer)
    q6 = Column(Integer)
    q7 = Column(Integer)
    q8 = Column(Integer)
    
    openEnded = Column(String, nullable=True)
    
    # Tự động thêm ngày giờ khi một bản ghi được tạo
    created_at = Column(DateTime(timezone=True), server_default=func.now())