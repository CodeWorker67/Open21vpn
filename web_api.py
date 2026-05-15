"""
HTTP API для кастомной страницы подписки: создание платежей с source=subpage в payload.

Обычно сервер поднимается вместе с ботом из main.py (если задан SUB_PAGE_API_KEY).
Отдельно: python web_api.py (тот же .env).

Заголовок: X-API-Key: значение SUB_PAGE_API_KEY из .env
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Literal, Optional

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from config import ADMIN_IDS, BOT_URL, SUB_PAGE_API_KEY, WEB_API_PORT
from config_bd.models import create_tables
from lexicon import dct_desc, dct_price
from logging_config import logger
from payments.pay_cryptobot import create_cryptobot_payment
from payments.pay_freekassa import pay as fk_pay
from payments.pay_stars import get_stars_amount, send_stars_subscription_invoice

SUBPAGE_SOURCE = "subpage"

# СБП (подписная страница): 7 / 180 / 3000 не продаются из бота — цены только здесь (при необходимости поменяйте).
FK_SBP_SUBPAGE_PRICE_RUB: dict[str, int] = {
    "7": 99,
    "30": dct_price["30"],
    "90": dct_price["90"],
    "180": 849,
    "3000": 12999,
}

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_subpage_api_key(x_api_key: Optional[str] = Depends(api_key_header)) -> None:
    if not SUB_PAGE_API_KEY:
        raise HTTPException(status_code=503, detail="SUB_PAGE_API_KEY is not configured")
    if not x_api_key or x_api_key != SUB_PAGE_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")


class FkSbpPayBody(BaseModel):
    user_id: int = Field(..., description="Telegram user id")
    duration: Literal["7", "30", "90", "180", "3000"]


class FkCardPayBody(BaseModel):
    user_id: int = Field(..., description="Telegram user id")
    duration: Literal["30", "90", "240"]


class StarsPayBody(BaseModel):
    user_id: int = Field(..., description="Telegram user id")
    duration: Literal["30", "90", "240"]


class CryptobotPayBody(BaseModel):
    user_id: int = Field(..., description="Telegram user id")
    duration: Literal["30", "90", "240"]


class PayUrlResponse(BaseModel):
    """Ссылка на оплату; для Stars в url — ссылка на бота (счёт приходит в Telegram)."""

    url: str
    payment_id: Optional[str] = None


def _fk_subpage_description(duration: str) -> str:
    if duration in dct_desc:
        return dct_desc[duration]
    return f"Open 21 VPN — {duration} дней (подписная страница)"


@asynccontextmanager
async def _lifespan(_: FastAPI):
    await create_tables()
    yield


router = APIRouter(
    prefix="/api/v1/sub_page/pay",
    tags=["sub_page"],
    dependencies=[Depends(require_subpage_api_key)],
)


@router.post("/fk_sbp", response_model=PayUrlResponse)
async def sub_page_pay_fk_sbp(body: FkSbpPayBody) -> PayUrlResponse:
    rub = FK_SBP_SUBPAGE_PRICE_RUB.get(body.duration)
    if rub is None:
        raise HTTPException(status_code=400, detail="Unknown SBP duration")
    uid = str(body.user_id)
    desc = _fk_subpage_description(body.duration)
    info = await fk_pay(
        val=str(rub),
        des=desc,
        user_id=uid,
        duration=body.duration,
        white=False,
        ui_kind="sbp",
        source=SUBPAGE_SOURCE,
    )
    if info.get("status") != "pending" or not info.get("url"):
        logger.error(f"sub_page fk_sbp failed user={body.user_id} duration={body.duration}")
        raise HTTPException(status_code=502, detail="FreeKassa: could not create payment")
    return PayUrlResponse(url=info["url"], payment_id=info.get("id"))


@router.post("/fk_card", response_model=PayUrlResponse)
async def sub_page_pay_fk_card(body: FkCardPayBody) -> PayUrlResponse:
    rub = dct_price[body.duration]
    uid = str(body.user_id)
    desc = dct_desc[body.duration]
    info = await fk_pay(
        val=str(rub),
        des=desc,
        user_id=uid,
        duration=body.duration,
        white=False,
        ui_kind="card",
        source=SUBPAGE_SOURCE,
    )
    if info.get("status") != "pending" or not info.get("url"):
        logger.error(f"sub_page fk_card failed user={body.user_id} duration={body.duration}")
        raise HTTPException(status_code=502, detail="FreeKassa: could not create payment")
    return PayUrlResponse(url=info["url"], payment_id=info.get("id"))


@router.post("/stars", response_model=PayUrlResponse)
async def sub_page_pay_stars(body: StarsPayBody) -> PayUrlResponse:
    if not BOT_URL:
        raise HTTPException(status_code=503, detail="BOT_URL is not configured")
    stars_amount = int(get_stars_amount("Stars", body.duration))
    if body.user_id in ADMIN_IDS:
        stars_amount = 1
    try:
        await send_stars_subscription_invoice(
            body.user_id,
            duration_days_str=body.duration,
            stars_amount=stars_amount,
            white_flag=False,
            gift_flag=False,
            source=SUBPAGE_SOURCE,
        )
    except Exception as e:
        logger.error(f"sub_page stars invoice user={body.user_id}: {e}")
        raise HTTPException(status_code=502, detail="Could not send Telegram Stars invoice") from e
    return PayUrlResponse(url=BOT_URL, payment_id=None)


@router.post("/cryptobot", response_model=PayUrlResponse)
async def sub_page_pay_cryptobot(body: CryptobotPayBody) -> PayUrlResponse:
    rub = dct_price[body.duration]
    desc = dct_desc[body.duration]
    result = await create_cryptobot_payment(
        rub_amount=rub,
        description=desc,
        user_id=body.user_id,
        duration=body.duration,
        white=False,
        is_gift=False,
        source=SUBPAGE_SOURCE,
    )
    if result.get("status") != "pending" or not result.get("url"):
        logger.error(f"sub_page cryptobot failed user={body.user_id}: {result}")
        raise HTTPException(status_code=502, detail="Cryptobot: could not create invoice")
    inv = result.get("invoice_id")
    pid = str(inv) if inv is not None else None
    return PayUrlResponse(url=result["url"], payment_id=pid)


app = FastAPI(title="Open21 VPN — subpage payments", lifespan=_lifespan)
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    if not SUB_PAGE_API_KEY:
        raise SystemExit("В .env задайте SUB_PAGE_API_KEY для защиты API")
    uvicorn.run("web_api:app", host="0.0.0.0", port=WEB_API_PORT, reload=False)
