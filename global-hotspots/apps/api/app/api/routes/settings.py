from fastapi import APIRouter, Depends
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.api.deps import current_user, db_session
from app.core.crypto import encrypt_value, masked_preview
from app.models.ai_provider_key import AIProviderKey
from app.models.runtime_setting import RuntimeSetting
from app.models.user import User
from app.schemas.settings import ProviderItem, RuntimeProxyIn, RuntimeProxyOut, UpsertAIKeyIn


router = APIRouter(prefix="/settings", tags=["settings"])


@router.post("/ai-key", response_model=ProviderItem)
def upsert_ai_key(
    payload: UpsertAIKeyIn,
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> ProviderItem:
    item = db.scalar(
        select(AIProviderKey).where(and_(AIProviderKey.user_id == user.id, AIProviderKey.provider == payload.provider))
    )
    if payload.is_default:
        for row in db.scalars(select(AIProviderKey).where(AIProviderKey.user_id == user.id)).all():
            row.is_default = False

    if not item:
        item = AIProviderKey(
            user_id=user.id,
            provider=payload.provider,
            api_key_encrypted=encrypt_value(payload.api_key),
            model=payload.model,
            base_url=payload.base_url,
            is_default=payload.is_default,
        )
        db.add(item)
    else:
        item.api_key_encrypted = encrypt_value(payload.api_key)
        item.model = payload.model
        item.base_url = payload.base_url
        item.is_default = payload.is_default

    db.commit()
    return ProviderItem(
        provider=item.provider,
        model=item.model,
        base_url=item.base_url,
        is_default=item.is_default,
        key_preview=masked_preview(payload.api_key),
    )


@router.get("/ai-providers", response_model=list[ProviderItem])
def list_ai_providers(user: User = Depends(current_user), db: Session = Depends(db_session)) -> list[ProviderItem]:
    rows = db.scalars(select(AIProviderKey).where(AIProviderKey.user_id == user.id)).all()
    items: list[ProviderItem] = []
    for row in rows:
        items.append(
            ProviderItem(
                provider=row.provider,
                model=row.model,
                base_url=row.base_url,
                is_default=row.is_default,
                key_preview="****",
            )
        )
    return items


@router.get("/runtime/proxy", response_model=RuntimeProxyOut)
def get_runtime_proxy(user: User = Depends(current_user), db: Session = Depends(db_session)) -> RuntimeProxyOut:
    _ = user
    row = db.scalar(select(RuntimeSetting).where(RuntimeSetting.key == "source_proxy_url"))
    return RuntimeProxyOut(source_proxy_url=row.value if row else None)


@router.post("/runtime/proxy", response_model=RuntimeProxyOut)
def set_runtime_proxy(
    payload: RuntimeProxyIn,
    user: User = Depends(current_user),
    db: Session = Depends(db_session),
) -> RuntimeProxyOut:
    _ = user
    row = db.scalar(select(RuntimeSetting).where(RuntimeSetting.key == "source_proxy_url"))
    value = (payload.source_proxy_url or "").strip()
    if not row:
        row = RuntimeSetting(key="source_proxy_url", value=value)
        db.add(row)
    else:
        row.value = value
    db.commit()
    return RuntimeProxyOut(source_proxy_url=value or None)
