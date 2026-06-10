import urllib.parse
from typing import List, Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import CHANEL_URL, BOT_URL
from lexicon import dct_desc

STYLE_PRIMARY = "primary"
STYLE_SUCCESS = "success"
STYLE_DANGER = "danger"

BTN_BACK = "🔙 Назад"

SITE_URL = "https://open21.top/"
OPEN_SITE_CB = "open_site"

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


_STYLES_TRIAL = {
    "trial_pay": STYLE_SUCCESS,
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


def _append_open_site_row(markup: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
    rows = list(markup.inline_keyboard)
    rows.append(
        [
            InlineKeyboardButton(
                text="🌐 Наш сайт",
                callback_data=OPEN_SITE_CB,
                style=STYLE_PRIMARY,
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


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
        buy_vpn="🛒 Купить от 199₽ в месяц",
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
    markup = _append_open_site_row(markup)
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


def keyboard_buy_device_tier(*, with_trial: bool = False):
    kwargs = {
        "buy_tier_3": "🔹 Тарифы на 3️⃣ устройства",
        "buy_tier_5": "🔸 Тарифы на 5️⃣ устройств",
        "buy_tier_10": "🏆 Тарифы на 🔟 устройств",
        "back_to_main": BTN_BACK,
    }
    styles = {
        "buy_tier_3": STYLE_PRIMARY,
        "buy_tier_5": STYLE_PRIMARY,
        "buy_tier_10": STYLE_SUCCESS,
        "back_to_main": STYLE_PRIMARY,
    }
    if with_trial:
        kwargs = {"trial_pay": "✨ Попробовать 3 дня за 1₽", **kwargs}
        styles["trial_pay"] = STYLE_SUCCESS
    return create_kb(1, styles=styles, **kwargs)


def keyboard_tariff_bonus():
    return keyboard_buy_device_tier(with_trial=True)


def keyboard_tariff():
    return keyboard_buy_device_tier(with_trial=True)


def keyboard_tariff_trial():
    return keyboard_buy_device_tier(with_trial=True)


def _styles_buy_duration(devices: int) -> dict[str, str]:
    st: dict[str, str] = {"back_buy_tier": STYLE_PRIMARY}
    for months in (1, 3, 6, 12):
        key = f"r_m{months}_d{devices}"
        st[key] = STYLE_SUCCESS if months >= 6 else STYLE_PRIMARY
    return st


def keyboard_buy_duration(devices: int) -> InlineKeyboardMarkup:
    kwargs: dict[str, str] = {}
    for months in (1, 3, 6, 12):
        ck = f"r_m{months}_d{devices}"
        dk = f"m{months}_d{devices}"
        kwargs[ck] = dct_desc[dk]
    kwargs["back_buy_tier"] = BTN_BACK
    return create_kb(1, styles=_styles_buy_duration(devices), **kwargs)


def keyboard_gift_device_tier():
    return create_kb(
        1,
        styles={
            "gift_tier_3": STYLE_PRIMARY,
            "gift_tier_5": STYLE_PRIMARY,
            "gift_tier_10": STYLE_SUCCESS,
        },
        gift_tier_3="🔹 Тарифы на 3️⃣ устройства",
        gift_tier_5="🔸 Тарифы на 5️⃣ устройств",
        gift_tier_10="🏆 Тарифы на 🔟 устройств",
        back_to_main=BTN_BACK,
    )


def _styles_gift_duration(devices: int) -> dict[str, str]:
    st: dict[str, str] = {"gift_back_tier": STYLE_PRIMARY}
    for months in (1, 3, 6, 12):
        key = f"gift_r_m{months}_d{devices}"
        st[key] = STYLE_SUCCESS if months >= 6 else STYLE_PRIMARY
    return st


def keyboard_gift_duration(devices: int) -> InlineKeyboardMarkup:
    kwargs: dict[str, str] = {}
    for months in (1, 3, 6, 12):
        ck = f"gift_r_m{months}_d{devices}"
        dk = f"m{months}_d{devices}"
        kwargs[ck] = dct_desc[dk]
    kwargs["gift_back_tier"] = BTN_BACK
    return create_kb(1, styles=_styles_gift_duration(devices), **kwargs)


def keyboard_gift_tariff():
    return keyboard_gift_device_tier()


def keyboard_subscription(links: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    """links: (текст кнопки, https-ссылка на подписку)."""
    buttons = []
    for text, url in links:
        if not url:
            continue
        buttons.append(
            [
                InlineKeyboardButton(
                    text=text[:64],
                    url=url,
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


def keyboard_import_sub(app_callback: str, subscriptions: list[tuple[str, str]]):
    """subscriptions: (slot_key, текст кнопки)."""
    buttons = []
    for slot, label in subscriptions:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=label[:64],
                    callback_data=f"{app_callback}_{slot}",
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
