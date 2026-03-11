from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

app = FastAPI()

# CORS 설정: 브라우저에서의 자유로운 통신을 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 파일 경로 설정 (Vercel 서버리스 환경 대응)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POS_DATA = os.path.join(BASE_DIR, "pos_data.csv")
ERP_DATA = os.path.join(BASE_DIR, "erp_data.csv")

# 사용자 정보 및 시스템별 토큰
ADMIN_USER = {"username": "admin", "password": "1234"}
AUTH_TOKENS = {
    "POS": "token-pos-777",
    "ERP": "token-erp-888"
}

# ERP 시스템 내 발주서 저장 공간 (메모리 DB)
erp_po_records = []

# [1] 시스템별 로그인 API (pos 또는 erp로 구분)
@app.post("/api/login/{system}")
async def login(system: str, data: dict):
    system_key = system.upper()
    if data.get("username") == ADMIN_USER["username"] and \
       data.get("password") == ADMIN_USER["password"]:
        return {"success": True, "token": AUTH_TOKENS.get(system_key)}
    raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 틀렸습니다.")

# [2] POS 시스템 판매 데이터 조회 API
@app.get("/api/pos/sales")
async def get_pos_sales(authorization: str = Header(None)):
    if authorization != f"Bearer {AUTH_TOKENS['POS']}":
        raise HTTPException(status_code=403, detail="POS 시스템 권한이 없습니다.")
    
    if not os.path.exists(POS_DATA):
        raise HTTPException(status_code=404, detail="POS 데이터 파일을 찾을 수 없습니다.")
        
    df = pd.read_csv(POS_DATA, encoding='utf-8-sig')
    return df.to_dict(orient="records")

# [3] ERP 시스템 재고 조회 API
@app.get("/api/erp/inventory")
async def get_erp_inventory(authorization: str = Header(None)):
    if authorization != f"Bearer {AUTH_TOKENS['ERP']}":
        raise HTTPException(status_code=403, detail="ERP 시스템 권한이 없습니다.")
    
    if not os.path.exists(ERP_DATA):
        raise HTTPException(status_code=404, detail="ERP 데이터 파일을 찾을 수 없습니다.")
        
    df = pd.read_csv(ERP_DATA, encoding='utf-8-sig')
    return df.to_dict(orient="records")

# [4] ERP 시스템 발주서 접수 API (Make 에이전트 또는 담당자가 호출)
@app.post("/api/erp/po/create")
async def create_po(data: dict, authorization: str = Header(None)):
    if authorization != f"Bearer {AUTH_TOKENS['ERP']}":
        raise HTTPException(status_code=403, detail="ERP 시스템 권한이 없습니다.")
    
    # 발주 데이터 저장
    erp_po_records.append(data)
    return {"success": True, "message": "ERP에 발주서가 성공적으로 접수되었습니다."}
