from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from bot import bot, sql
from config import YOUKASSA_API_KEY, YOUKASSA_SHOP_ID
from keyboard import keyboard_payment_cancel
from lexicon import TRIAL_TARIFF_PAYMENT_RUB, lexicon
from logging_config import logger
from payments.pay_youkassa import create_youkassa_autorenew_payment, yk_get_payment
from payments.process_payload import process_confirmed_payment

YK_PENDING_MAX_AGE = timedelta(hours=24)


def _coerce_payload_auto_renew(payload: Optional[str]) -> bool:
    if not payload:
        return False
    parts: Dict[str, str] = {}
    for item in str(payload).split(","):
        item = item.strip()
        if ":" not in item:
            continue
        k, _, v = item.partition(":")
        parts[k.strip()] = v.strip()
    return parts.get("auto_renew", "False") == "True"


def _coerce_payload_is_trial(payload: Optional[str]) -> bool:
    if not payload:
        return False
    parts: Dict[str, str] = {}
    for item in str(payload).split(","):
        item = item.strip()
        if ":" not in item:
            continue
        k, _, v = item.partition(":")
        parts[k.strip()] = v.strip()
    try:
        duration = int(parts.get("duration", -1))
        amt = int(float(parts.get("amount", -1)))
    except (ValueError, TypeError):
        return False
    return duration == 3 and amt in (TRIAL_TARIFF_PAYMENT_RUB, 10)


def _payment_method_id_from_yk(data: Dict[str, Any]) -> Optional[str]:
    pm = data.get("payment_method")
    if isinstance(pm, dict):
        pid = pm.get("id")
        if pid:
            return str(pid)
    return None


def _yk_status_local(api_status: str) -> str:
    s = (api_status or "").lower()
    if s == "succeeded":
        return "confirmed"
    if s == "canceled":
        return "canceled"
    return "pending"


def _yk_payment_timed_out(time_created: Optional[datetime]) -> bool:
    if time_created is None:
        return False
    return datetime.now() - time_created >= YK_PENDING_MAX_AGE


async def check_youkassa_payments():
    if not YOUKASSA_SHOP_ID or not YOUKASSA_API_KEY:
        return
    await _poll_pending_youkassa()
    await _maybe_autorenew_subscriptions()


async def _poll_pending_youkassa():
    pending = await sql.get_pending_youkassa_payments()
    if not pending:
        return
    logger.info(f"ЮKassa: проверка {len(pending)} pending")
    for payment in pending:
        tid = payment.transaction_id
        if not tid:
            continue
        try:
            row = await yk_get_payment(tid)
        except Exception as e:
            logger.error(f"ЮKassa get {tid}: {e}")
            continue
        api_status = str(row.get("status") or "")
        new_local = _yk_status_local(api_status)
        if new_local == "pending" and _yk_payment_timed_out(payment.time_created):
            new_local = "canceled"
        if new_local == payment.status:
            continue
        await sql.update_youkassa_payment_status(tid, new_local)
        logger.info(f"ЮKassa {tid}: {payment.status} → {new_local}")

        if new_local == "confirmed":
            pm_id = _payment_method_id_from_yk(row)
            if pm_id:
                await sql.update_user_yookassa_payment_method(payment.user_id, pm_id)
            payload = payment.payload or ""
            if _coerce_payload_is_trial(payload):
                await sql.update_user_yookassa_autopay_enabled(payment.user_id, True)
            await process_confirmed_payment(payload)
            if _coerce_payload_auto_renew(payload):
                await sql.clear_yookassa_autorenew_cooldown(payment.user_id)
        elif new_local == "canceled":
            payload = payment.payload or ""
            if _coerce_payload_auto_renew(payload):
                await sql.set_yookassa_autorenew_cooldown(
                    payment.user_id,
                    datetime.now() + timedelta(days=1),
                )
            elif not payment.is_gift:
                try:
                    await bot.send_message(
                        payment.user_id,
                        lexicon["payment_cancel"],
                        reply_markup=keyboard_payment_cancel(),
                    )
                except Exception as e:
                    logger.error(f"ЮKassa cancel notify {payment.user_id}: {e}")


async def _maybe_autorenew_subscriptions():
    rows = await sql.select_users_for_yookassa_autorenew()
    if not rows:
        return
    for user_id, pm_id in rows:
        if not pm_id:
            continue
        if await sql.user_has_pending_youkassa_autorenew(int(user_id)):
            continue
        pid = await create_youkassa_autorenew_payment(int(user_id), str(pm_id))
        if pid:
            logger.info(f"ЮKassa autorenew: создан платёж {pid} user={user_id}")


check_youkassa = check_youkassa_payments
