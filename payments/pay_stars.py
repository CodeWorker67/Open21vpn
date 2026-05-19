from typing import Optional

from bot import bot
from config import ADMIN_IDS
from keyboard import keyboard_payment_stars
from logging_config import logger

from aiogram import Router, F
from aiogram.types import CallbackQuery, LabeledPrice, PreCheckoutQuery, Message
from lexicon import lexicon
from payments.process_payload import process_confirmed_payment


router: Router = Router()


def get_stars_amount(currency: str, duration: str) -> float:
    """Возвращает цену для тарифа в указанной криптовалюте"""
    prices = {
        'Stars': {'30': 349, '90': 749, '365': 1799, '240': 1799, 'white_30': 299}
    }
    return prices.get(currency, {}).get(duration, 0)


async def send_stars_subscription_invoice(
    chat_id: int,
    *,
    duration_days_str: str,
    stars_amount: int,
    white_flag: bool,
    gift_flag: bool,
    source: Optional[str] = None,
) -> None:
    """Счёт Stars в Telegram (бот должен быть запущен с polling / webhook)."""
    user_id = str(chat_id)
    payload = (
        f"user_id:{user_id},duration:{duration_days_str},white:{white_flag},"
        f"gift:{gift_flag},method:stars,amount:{stars_amount}"
    )
    if source:
        payload += f",source:{source}"
    prices = [LabeledPrice(label="XTR", amount=stars_amount)]
    title = f"Оплата подписки {'в подарок другу ' if gift_flag else ''}на {duration_days_str} дней."
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
    if duration_key == '240':
        duration_key = '365'

    stars_amount = int(get_stars_amount('Stars', duration_key))
    if callback.from_user.id in ADMIN_IDS:
        stars_amount = 1

    duration_days = duration_key
    if 'white' in duration_days:
        duration_days = duration_days.replace('white_', '')
        white_flag = True
    if 'old' in duration_days:
        duration_days = duration_days.replace('old', '')

    await send_stars_subscription_invoice(
        callback.from_user.id,
        duration_days_str=duration_days,
        stars_amount=stars_amount,
        white_flag=white_flag,
        gift_flag=gift_flag,
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
