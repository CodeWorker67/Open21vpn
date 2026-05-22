import urllib.parse
from typing import List, Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import CHANEL_URL, BOT_URL
from lexicon import TARIFF_BTN_R_30, TARIFF_BTN_R_90, TARIFF_BTN_R_365

STYLE_PRIMARY = "primary"
STYLE_SUCCESS = "success"
STYLE_DANGER = "danger"

BTN_BACK = "🔙 Назад"

_DEFAULT_CALLBACK_STYLES: dict[str, str] = {
    "buy_vpn": STYLE_SUCCESS,
    "free_vpn": STYLE_SUCCESS,
    "trial_pay": STYLE_SUCCESS,
    "my_account": STYLE_SUCCESS,
    "connect_vpn": STYLE_PRIMARY,
    "ref": STYLE_PRIMARY,
    "buy_gift": STYLE_SUCCESS,
    "start_gift": STYLE_SUCCESS,
    "r_white_30": STYLE_PRIMARY,
}


def create_kb(
    width: int,
    *,
    styles: Optional[dict[str, str]] = None,
    **kwargs: str,
) -> InlineKeyboardMarkup:
    """
    Создаёт инлайн-клавиатуру. kwargs: callback_data -> текст кнопки.
    styles и встроенные дефолты задают цвет (primary | success | danger) в поддерживаемых клиентах.
    """
    kb_builder = InlineKeyboardBuilder()
    buttons: List[InlineKeyboardButton] = []
    merged = {**_DEFAULT_CALLBACK_STYLES, **(styles or {})}

    for button_data, button_text in kwargs.items():
        st = merged.get(button_data)
        if st:
            buttons.append(
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=button_data,
                    style=st,
                )
            )
        else:
            buttons.append(
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=button_data,
                )
            )

    kb_builder.row(*buttons, width=width)
    return kb_builder.as_markup()


_STYLES_TARIFF = {
    "r_30": STYLE_PRIMARY,
    "r_90": STYLE_PRIMARY,
    "r_365": STYLE_SUCCESS,
    "r_white_30": STYLE_PRIMARY,
    "trial_pay": STYLE_SUCCESS,
}

_STYLES_GIFT = {
    "gift_r_30": STYLE_PRIMARY,
    "gift_r_90": STYLE_PRIMARY,
    "gift_r_365": STYLE_SUCCESS,
}


def chanel_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="👉Подписаться на канал",
                url=CHANEL_URL,
                style=STYLE_PRIMARY,
            )
        ]
    ])
    return keyboard


def _append_partner_earn_row(markup: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
    rows = list(markup.inline_keyboard)
    rows.append(
        [
            InlineKeyboardButton(
                text="💸 Зарабатывай с нами",
                callback_data="partner_earn",
                style=STYLE_SUCCESS,
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def keyboard_start_bonus():
    markup = create_kb(
        1,
        styles={"trial_pay": STYLE_SUCCESS, "buy_vpn": STYLE_PRIMARY},
        trial_pay="✨ Попробовать 3 дня за 1₽",
        buy_vpn="🛒 Купить от 150₽ в месяц",
    )
    return _append_partner_earn_row(markup)


def keyboard_start():
    markup = create_kb(
        1,
        my_account="👤 Мой аккаунт",
        buy_vpn="🛒 Купить подписку",
        connect_vpn="🔗 Подключить Open 21 VPN",
        ref="👥 Бесплатный VPN за приглашения",
        buy_gift="🎁 Подарить подписку",
    )
    return _append_partner_earn_row(markup)


def keyboard_my_account(*, autopay_on: bool) -> InlineKeyboardMarkup:
    back = "🔙 Назад"
    if autopay_on:
        return create_kb(
            1,
            styles={
                "account_autopay_off": STYLE_DANGER,
                "back_to_main": STYLE_PRIMARY,
            },
            account_autopay_off="🚫 Отключить автоплатежи",
            back_to_main=back,
        )
    return create_kb(
        1,
        styles={
            "account_autopay_on": STYLE_SUCCESS,
            "back_to_main": STYLE_PRIMARY,
        },
        account_autopay_on="✅ Включить автоплатежи",
        back_to_main=back,
    )


def keyboard_tariff_bonus():
    return create_kb(
        1,
        styles=_STYLES_TARIFF,
        r_30=TARIFF_BTN_R_30,
        r_90=TARIFF_BTN_R_90,
        r_365=TARIFF_BTN_R_365,
        trial_pay="✨ Попробовать 3 дня за 1₽",
        back_to_main="🔙 Назад",
    )


def keyboard_tariff():
    return create_kb(
        1,
        styles=_STYLES_TARIFF,
        r_30=TARIFF_BTN_R_30,
        r_90=TARIFF_BTN_R_90,
        r_365=TARIFF_BTN_R_365,
        trial_pay="✨ Попробовать 3 дня за 1₽",
        # r_white_30="🦾 Ускоритель игр Mobile - 299 руб",
        back_to_main="🔙 Назад",
    )


def keyboard_tariff_trial():
    """Тарифы для пушей до конца подписки у пользователей без полной оплаты (reserve_field=False)."""
    return create_kb(
        1,
        styles={k: v for k, v in _STYLES_TARIFF.items() if k != "trial_pay"},
        r_30=TARIFF_BTN_R_30,
        r_90=TARIFF_BTN_R_90,
        r_365=TARIFF_BTN_R_365,
        trial_pay="✨ Попробовать 3 дня за 1₽",
        back_to_main="🔙 Назад",
    )


def keyboard_gift_tariff():
    return create_kb(
        1,
        styles=_STYLES_GIFT,
        gift_r_30=TARIFF_BTN_R_30,
        gift_r_90=TARIFF_BTN_R_90,
        gift_r_365=TARIFF_BTN_R_365,
        back_to_main="🔙 Назад",
    )


def keyboard_subscription(sub_url, sub_url_white):
    buttons = []
    if sub_url:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="💫 Ваша подписка на VPN",
                    url=sub_url,
                    style=STYLE_PRIMARY,
                )
            ]
        )
    if sub_url_white:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="🦾 Мобильный тариф",
                    url=sub_url_white,
                    style=STYLE_PRIMARY,
                )
            ]
        )
    buttons.append(
        [
            InlineKeyboardButton(
                text="❌ Если страница не загружается",
                callback_data="import",
                style=STYLE_DANGER,
            )
        ]
    )
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def keyboard_sub_after_buy(sub_url):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 В личный кабинет",
                    url=sub_url,
                    style=STYLE_PRIMARY,
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Если страница не загружается",
                    callback_data="import",
                    style=STYLE_DANGER,
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎁 Подарить подписку",
                    callback_data="buy_gift",
                    style=STYLE_SUCCESS,
                )
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")],
        ]
    )
    return keyboard


def keyboard_sub_after_free(sub_url):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 В личный кабинет",
                    url=sub_url,
                    style=STYLE_PRIMARY,
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Если страница не загружается",
                    callback_data="import",
                    style=STYLE_DANGER,
                )
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")],
        ]
    )
    return keyboard


def keyboard_import_os():
    return create_kb(
        1,
        styles={
            "import_android": STYLE_PRIMARY,
            "import_ios": STYLE_PRIMARY,
            "import_windows": STYLE_PRIMARY,
            "import_macos": STYLE_PRIMARY,
        },
        import_android="🤖 Android",
        import_ios="🍎 iOS",
        import_windows="🖥️ Windows",
        import_macos="🍏 MacOS",
        back_to_main="🔙 Назад",
    )


def keyboard_import_app(os_callback: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐️ Happ",
                    callback_data=f"{os_callback}_happ",
                    style=STYLE_PRIMARY,
                )
            ],
            [
                InlineKeyboardButton(
                    text="📡 V2raytun",
                    callback_data=f"{os_callback}_v2",
                    style=STYLE_PRIMARY,
                )
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")],
        ]
    )


def keyboard_import_sub(app_callback: str, has_casual: bool, has_white: bool):
    buttons = []
    if has_casual:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="💫 Ваша подписка на VPN",
                    callback_data=f"{app_callback}_casual",
                    style=STYLE_PRIMARY,
                )
            ]
        )
    if has_white:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="🦾 Мобильный тариф",
                    callback_data=f"{app_callback}_white",
                    style=STYLE_PRIMARY,
                )
            ]
        )
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def keyboard_import_end(url_app: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📥 Скачать приложение",
                    url=url_app,
                    style=STYLE_PRIMARY,
                )
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")],
        ]
    )


def keyboard_payment_cancel():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛒 Купить подписку",
                    callback_data="buy_vpn",
                    style=STYLE_PRIMARY,
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎁 Подарить подписку",
                    callback_data="start_gift",
                    style=STYLE_SUCCESS,
                )
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")],
        ]
    )
    return keyboard


def keyboard_payment_method_trial(tarif):
    """ЮKassa только для пробного тарифа."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚡ СБП (ЮKassa)",
                    callback_data=f"yk_sbp_{tarif}",
                    style=STYLE_SUCCESS,
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 Карта (ЮKassa)",
                    callback_data=f"yk_card_{tarif}",
                    style=STYLE_PRIMARY,
                )
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")],
        ]
    )


def keyboard_payment_method(tarif):
    rows = [
        [
            InlineKeyboardButton(
                text="⚡ СБП",
                callback_data=f"wata_sbp_{tarif}",
                style=STYLE_SUCCESS,
            )
        ],
    ]
    rows.append(
        [
            InlineKeyboardButton(
                text="💳 Карта РФ",
                callback_data=f"wata_card_{tarif}",
                style=STYLE_PRIMARY,
            )
        ]
    )
    rows.extend(
        [
            [
                InlineKeyboardButton(
                    text="⭐️ Telegram Stars",
                    callback_data=f"stars_{tarif}",
                    style=STYLE_PRIMARY,
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 Crypto bot",
                    callback_data=f"crypto_{tarif}",
                    style=STYLE_PRIMARY,
                )
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def keyboard_payment_method_stock(tarif):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚡ СБП",
                    callback_data=f"wata_sbp_{tarif}",
                    style=STYLE_SUCCESS,
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 Карта РФ",
                    callback_data=f"wata_card_{tarif}",
                    style=STYLE_PRIMARY,
                )
            ],
            [
                InlineKeyboardButton(
                    text="⭐️ Telegram Stars",
                    callback_data=f"stars_{tarif}",
                    style=STYLE_PRIMARY,
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 Crypto bot",
                    callback_data=f"crypto_{tarif}",
                    style=STYLE_PRIMARY,
                )
            ],
        ]
    )
    return keyboard


def keyboard_payment_sbp(text, pay_url):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=text,
                    url=pay_url,
                    style=STYLE_SUCCESS,
                )
            ]
        ]
    )


def keyboard_payment_stars(stars_amount):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Оплатить {stars_amount} ⭐️",
                    pay=True,
                    style=STYLE_SUCCESS,
                )
            ]
        ]
    )


def ref_keyboard(user_id):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Пригласить друзей🫶",
                    url=f"https://t.me/share/url?url={BOT_URL}?start=ref{user_id}&text={urllib.parse.quote('Вот ссылка для тебя на надежный VPN!')}",
                    style=STYLE_SUCCESS,
                )
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")],
        ]
    )
    return keyboard


def keyboard_inline_ref(user_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔗 Подключить Open 21 VPN",
                    url=f"{BOT_URL}?start=ref{user_id}",
                    style=STYLE_PRIMARY,
                )
            ]
        ]
    )


def keyboard_partner_intro():
    return create_kb(
        1,
        styles={
            "partner_create_link": STYLE_SUCCESS,
            "back_to_main": STYLE_PRIMARY,
        },
        partner_create_link='🔗 Создать партнёрскую ссылку',
        back_to_main=BTN_BACK,
    )


def keyboard_partner_dashboard():
    return create_kb(
        1,
        styles={
            "partner_withdraw": STYLE_SUCCESS,
            "back_to_main": STYLE_PRIMARY,
        },
        partner_withdraw='💰 Создать заявку на вывод',
        back_to_main=BTN_BACK,
    )


def keyboard_partner_withdraw(support_url: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💬 Вывести деньги",
                url=support_url,
                style=STYLE_SUCCESS,
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="partner_earn",
                style=STYLE_PRIMARY,
            )
        ],
    ])
