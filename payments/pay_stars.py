from typing import Optional

from bot import bot
from config import ADMIN_IDS
from keyboard import keyboard_payment_stars
from logging_config import logger

from aiogram import Router, F
from aiogram.types import CallbackQuery, LabeledPrice, PreCheckoutQuery, Message
from lexicon import dct_price, lexicon, payment_tariff_summary_pro
from payments.process_payload import process_confirmed_payment
from tariff_resolve import tariff_days_for_x3, device_from_tariff_key


router: Router = Router()


async def send_stars_subscription_invoice(
    chat_id: int,
    *,
    duration_days_str: str,
    stars_amount: int,
    white_flag: bool,
    gift_flag: bool,
    device_n: int = 5,
    source: Optional[str] = None,
    description: Optional[str] = None,
) -> None:
    """Счёт Stars в Telegram (бот должен быть запущен с polling / webhook)."""
    user_id = str(chat_id)
    payload = (
        f"user_id:{user_id},duration:{duration_days_str},white:{white_flag},"
        f"gift:{gift_flag},method:stars,amount:{stars_amount},device:{device_n}"
    )
    if source:
        payload += f",source:{source}"
    prices = [LabeledPrice(label="XTR", amount=stars_amount)]
    title = f"Оплата подписки {'в подарок другу ' if gift_flag else ''}на {duration_days_str} дней."
    if description is None:
        description = lexicon['payment_link_white'] if white_flag else lexicon['payment_link']
    await bot.send_invoice(
        chat_id,
        title=title,
        description=description,
        prices=prices,
        provider_token="",
        payload=payload,
        currency="XTR",
        reply_markup=keyboard_payment_stars(stars_amount),
    )


@router.callback_query(F.data.startswith('stars_'))
async def process_payment_stars(callback: CallbackQuery):
    gift_flag = False
    white_flag = False
    if 'gift_' in callback.data:
        gift_flag = True
    duration_key = callback.data.replace('stars_r_', '').replace('stars_gift_r_', '')

    white_flag = False
    if 'white' in duration_key:
        duration_plain = duration_key.replace('white_', '', 1)
        white_flag = True
    else:
        duration_plain = duration_key

    stars_amount = int(dct_price.get(duration_key, 0))
    if callback.from_user.id in ADMIN_IDS:
        stars_amount = 1

    days_payload = str(tariff_days_for_x3(duration_plain))
    device_n = device_from_tariff_key(duration_plain)

    if white_flag:
        description = lexicon['payment_link_white']
    else:
        description = payment_tariff_summary_pro(duration_key)

    await send_stars_subscription_invoice(
        callback.from_user.id,
        duration_days_str=days_payload,
        stars_amount=stars_amount,
        white_flag=white_flag,
        gift_flag=gift_flag,
        device_n=device_n,
        description=description,
    )


@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.content_type.in_({'successful_payment'}))
async def success_payment_handler(message: Message):
    payload = message.successful_payment.invoice_payload
    if not payload:
        logger.error(f"❌ Нет payload в платеже {message.successful_payment.invoice_payload}")
        return
    await process_confirmed_payment(payload)
