import hashlib
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.models.email_otp import EmailOtp
from app.models.user import User


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def issue_otp(db: Session, email: str) -> None:
    # 6位随机数
    code = "".join(str(random.randint(0, 9)) for _ in range(settings.otp_length))
    # 过期时间
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.otp_expire_minutes)
    # 创建email对象
    otp = EmailOtp(email=email, code_hash=_hash_code(code), expires_at=expires_at)
    db.add(otp)
    db.commit()
    print(f"[OTP] email={email} code={code}")


def verify_otp(db: Session, email: str, code: str) -> str | None:
    now = datetime.now(timezone.utc)
    stmt = (
        select(EmailOtp)
        .where(EmailOtp.email == email)
        .where(EmailOtp.consumed_at.is_(None))
        .order_by(EmailOtp.id.desc())
    )
    otp = db.scalar(stmt)
    if not otp:
        return None
    # 已过期
    if otp.expires_at < now:
        return None
    # hash校验失败
    if otp.code_hash != _hash_code(code):
        return None
    # 消耗日期设置
    otp.consumed_at = now

    # 根据邮箱,记录用户
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        user = User(email=email)
        db.add(user)
        db.flush()

    db.commit()
    # 返回token
    return create_access_token(str(user.id))
