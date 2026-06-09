import base64
import json
import uuid
from typing import Any, Dict, Literal, Optional

import aiohttp
from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot import sql
from config import (
    ADMIN_IDS,
    BOT_URL,
    YOUKASSA_API_KEY,
    YOUKASSA_RECEIPT_EMAIL,
    YOUKASSA_RETURN_URL,
    YOUKASSA_SHOP_ID,
    YOUKASSA_TAX_SYSTEM_CODE,
    YOUKASSA_VAT_CODE,
)
from keyboard import BTN_BACK, create_kb, keyboard_payment_sbp
from lexicon import RENEWAL_MONTH_PRICE_RUB, dct_desc, dct_price, lexicon
from logging_config import logger

YK_API = "https://api.yookassa.ru/v3"

router = Router()

YkForcedPm = Literal["sbp", "bank_card"]

TRIAL_CALLBACK_SUFFIX = "r_3"


def _return_url() -> str:
    u = (YOUKASSA_RETURN_URL or "").strip()
    if u.startswith("http"):
        return u
    b = (BOT_URL or "").strip()
    if b.startswith("http"):
        return b
    return "https://t.me"


def _yk_amount_str(rub: int) -> str:
    return f"{int(rub)}.00"


def _yk_customer_email(user_id: Optional[int] = None) -> str:
    if user_id is not None:
        return f"{int(user_id)}@telegram.org"
    return YOUKASSA_RECEIPT_EMAIL


def _yk_receipt(*, rub_amount: int, description: str, customer_email: str) -> Dict[str, Any]:
    """Чек для онлайн-кассы (обязателен, если в ЛК ЮKassa включена отправка чеков)."""
    item_desc = (description or "Услуги Open 21 VPN")[:128]
    receipt: Dict[str, Any] = {
        "customer": {"email": customer_email},
        "items": [
            {
                "description": item_desc,
                "quantity": "1.00",
                "amount": {"value": _yk_amount_str(rub_amount), "currency": "RUB"},
                "vat_code": YOUKASSA_VAT_CODE,
                "payment_mode": "full_payment",
                "payment_subject": "service",
            }
        ],
    }
    if YOUKASSA_TAX_SYSTEM_CODE is not None:
        receipt["tax_system_code"] = YOUKASSA_TAX_SYSTEM_CODE
    return receipt


def _auth_header() -> Dict[str, str]:
    if not YOUKASSA_SHOP_ID or not YOUKASSA_API_KEY:
        return {}
    raw = f"{YOUKASSA_SHOP_ID}:{YOUKASSA_API_KEY}"
    b64 = base64.b64encode(raw.encode("utf-8")).decode("ascii")
    return {
        "Authorization": f"Basic {b64}",
        "Content-Type": "application/json",
    }


async def _yk_request(method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = f"{YK_API}{path}"
    headers = {**_auth_header(), "Idempotence-Key": str(uuid.uuid4())}
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession() as session:
        req_kw: Dict[str, Any] = {"method": method, "url": url, "headers": headers, "timeout": timeout}
        if method.upper() != "GET" and body is not None:
            req_kw["json"] = body
        async with session.request(**req_kw) as resp:
            text = await resp.text()
            try:
                data = json.loads(text) if text else {}
            except json.JSONDecodeError:
                logger.error(f"ЮKassa не JSON {path}: {text[:500]}")
                raise
            if resp.status not in (200, 201):
                logger.error(f"ЮKassa {method} {path} {resp.status}: {text[:800]}")
                raise RuntimeError(f"ЮKassa HTTP {resp.status}: {text[:200]}")
            return data


async def yk_get_payment(payment_id: str) -> Dict[str, Any]:
    return await _yk_request("GET", f"/payments/{payment_id}", None)


async def yk_create_payment_redirect(
    *,
    rub_amount: int,
    description: str,
    save_payment_method: bool,
    payment_method_id: Optional[str] = None,
    forced_payment_method_type: Optional[YkForcedPm] = None,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    desc = (description or "Open 21 VPN")[:128]
    email = _yk_customer_email(user_id=user_id)
    pr: Dict[str, Any] = {
        "amount": {"value": _yk_amount_str(rub_amount), "currency": "RUB"},
        "capture": True,
        "description": desc,
        "receipt": _yk_receipt(rub_amount=rub_amount, description=desc, customer_email=email),
    }
    if payment_method_id:
        # Автосписание с сохранённой карты/СБП — без redirect confirmation.
        pr["payment_method_id"] = payment_method_id
    else:
        pr["confirmation"] = {"type": "redirect", "return_url": _return_url()}
        pr["save_payment_method"] = save_payment_method
        if forced_payment_method_type:
            pr["payment_method_data"] = {"type": forced_payment_method_type}
    return await _yk_request("POST", "/payments", pr)


def _confirmation_url(data: Dict[str, Any]) -> str:
    conf = data.get("confirmation") or {}
    return str(conf.get("confirmation_url") or "").strip()


def _normalize_yk_callback_to_yk_pay_form(data: str) -> str:
    if data.startswith("yk_sbp_"):
        return "yk_pay_" + data[len("yk_sbp_") :]
    if data.startswith("yk_card_"):
        return "yk_pay_" + data[len("yk_card_") :]
    return data


def _parse_tariff_callback(data: str) -> tuple[str, str, bool]:
    gift_flag = False
    if data.startswith("yk_pay_gift_r_"):
        gift_flag = True
        rest = data[len("yk_pay_gift_r_") :]
    elif data.startswith("yk_pay_r_"):
        rest = data[len("yk_pay_r_") :]
    else:
        rest = data.replace("yk_pay_", "", 1)
    desc_key = rest
    if "white" in rest:
        duration = rest.replace("white_", "")
    elif "old" in rest:
        duration = rest.replace("old", "")
    else:
        duration = rest
    return duration, desc_key, gift_flag


def _is_trial_yk_callback(data: str) -> bool:
    normalized = _normalize_yk_callback_to_yk_pay_form(data)
    _, desc_key, gift_flag = _parse_tariff_callback(normalized)
    if gift_flag:
        return False
    return desc_key == TRIAL_CALLBACK_SUFFIX or desc_key == "3"


async def _handle_youkassa_payment(callback: CallbackQuery, forced_pm: YkForcedPm) -> None:
    if not YOUKASSA_SHOP_ID or not YOUKASSA_API_KEY:
        await callback.answer()
        logger.error("ЮKassa: не заданы YOUKASSA_SHOP_ID / YOUKASSA_API_KEY")
        await callback.message.answer(lexicon["error_payment"], reply_markup=create_kb(1, back_to_main=BTN_BACK))
        return

    data = callback.data or ""
    if not _is_trial_yk_callback(data):
        await callback.answer(lexicon.get("yookassa_trial_only", "ЮKassa доступна только для пробного периода"), show_alert=True)
        return

    duration, desc_key, gift_flag = _parse_tariff_callback(_normalize_yk_callback_to_yk_pay_form(data))
    if gift_flag and str(duration) == "3":
        await callback.answer(lexicon.get("gift_no_trial", "Пробный период нельзя оформить в подарок"), show_alert=True)
        return

    await callback.answer()
    white_flag = "white" in desc_key
    try:
        rub_amount = int(dct_price[duration])
    except KeyError:
        logger.error(f"ЮKassa: неизвестный тариф duration={duration}")
        await callback.message.answer(lexicon["error_payment"], reply_markup=create_kb(1, back_to_main=BTN_BACK))
        return

    if callback.from_user.id in ADMIN_IDS:
        rub_amount = 1

    user_id = str(callback.from_user.id)
    method_payload = "yookassa_sbp" if forced_pm == "sbp" else "yookassa_card"
    payload = (
        f"user_id:{user_id},duration:{duration},white:{white_flag},gift:{gift_flag},"
        f"method:{method_payload},amount:{rub_amount},device:5,auto_renew:False"
    )
    desc = dct_desc.get(desc_key, f"Open 21 VPN пробный период {duration} дн.")

    try:
        pm = await yk_create_payment_redirect(
            rub_amount=rub_amount,
            description=desc[:128],
            save_payment_method=True,
            payment_method_id=None,
            forced_payment_method_type=forced_pm,
            user_id=callback.from_user.id,
        )
    except Exception as e:
        logger.error(f"ЮKassa create payment ({forced_pm}): {e}")
        await callback.message.answer(lexicon["error_payment"], reply_markup=create_kb(1, back_to_main=BTN_BACK))
        return

    pay_id = pm.get("id")
    if not pay_id:
        logger.error(f"ЮKassa: нет id в ответе {pm}")
        await callback.message.answer(lexicon["error_payment"], reply_markup=create_kb(1, back_to_main=BTN_BACK))
        return

    url = _confirmation_url(pm)
    if not url:
        logger.error(f"ЮKassa: нет confirmation_url {pm}")
        await callback.message.answer(lexicon["error_payment"], reply_markup=create_kb(1, back_to_main=BTN_BACK))
        return

    try:
        await sql.add_youkassa_payment(
            int(user_id),
            rub_amount,
            "pending",
            str(pay_id),
            payload,
            is_gift=gift_flag,
        )
    except Exception as e:
        logger.error(f"ЮKassa DB: {e}")
        await callback.message.answer(lexicon["error_payment"], reply_markup=create_kb(1, back_to_main=BTN_BACK))
        return

    text = lexicon["payment_link_trial"]
    btn = "⚡ Оплатить СБП" if forced_pm == "sbp" else "💳 Оплатить картой"
    channel = "СБП" if forced_pm == "sbp" else "карта"
    text += f"\n\nОплата через <b>ЮKassa</b> ({channel}):"

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard_payment_sbp(btn, url),
        )
    except Exception:
        await callback.message.answer(
            text=text,
            reply_markup=keyboard_payment_sbp(btn, url),
        )
    logger.info(
        f"ЮKassa: создан платёж ({forced_pm}) payment_id={pay_id} user={user_id} amount={rub_amount}"
    )


@router.callback_query(F.data.startswith("yk_sbp_"))
async def process_payment_youkassa_sbp(callback: CallbackQuery):
    await _handle_youkassa_payment(callback, "sbp")


@router.callback_query(F.data.startswith("yk_card_"))
async def process_payment_youkassa_card(callback: CallbackQuery):
    await _handle_youkassa_payment(callback, "bank_card")


async def create_youkassa_autorenew_payment(user_id: int, payment_method_id: str) -> Optional[str]:
    if not YOUKASSA_SHOP_ID or not YOUKASSA_API_KEY:
        return None
    rub = int(RENEWAL_MONTH_PRICE_RUB)
    if user_id in ADMIN_IDS:
        rub = 1
    desc = f"Автопродление Open 21 VPN, {rub} ₽ / 30 дней"[:128]
    payload = (
        f"user_id:{user_id},duration:30,white:False,gift:False,"
        f"method:yookassa,amount:{rub},device:5,auto_renew:True"
    )
    try:
        pm = await yk_create_payment_redirect(
            rub_amount=rub,
            description=desc,
            save_payment_method=False,
            payment_method_id=payment_method_id,
            user_id=user_id,
        )
    except Exception as e:
        logger.error(f"ЮKassa autorenew create: user={user_id} {e}")
        return None
    pay_id = pm.get("id")
    if not pay_id:
        return None
    try:
        await sql.add_youkassa_payment(
            user_id,
            rub,
            "pending",
            str(pay_id),
            payload,
            is_gift=False,
        )
    except Exception as e:
        logger.error(f"ЮKassa autorenew DB: {e}")
        return None
    return str(pay_id)
