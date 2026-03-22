from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session


from app.api.deps import db_session
from app.schemas.auth import AuthOut, RequestOtpIn, VerifyOtpIn
from app.services.auth import issue_otp, verify_otp


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/request-otp")
def request_otp(payload: RequestOtpIn, db: Session = Depends(db_session)) -> dict[str, str]:
    issue_otp(db, payload.email)
    return {"message": "OTP sent"}


@router.post("/verify-otp", response_model=AuthOut)
def verify(payload: VerifyOtpIn, db: Session = Depends(db_session)) -> AuthOut:
    token = verify_otp(db, payload.email, payload.code)
    if not token:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    return AuthOut(access_token=token)
