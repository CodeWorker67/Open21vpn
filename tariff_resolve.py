"""Цена и описание тарифа по ключу callback (в т.ч. m{N}_d{D}), число дней для панели X3."""
from __future__ import annotations

import re
from typing import Tuple

from lexicon import dct_desc, dct_price

_MONTHS_TO_DAYS = {1: 30, 3: 90, 6: 180, 12: 365}

DEFAULT_DEVICE_SLOTS = 5


def panel_username(user_id: int, *, white: bool, device_slots: int) -> str:
    """Username в панели: white → «id_white», иначе id / id_3 / id_10 (5 устройств — просто id)."""
    if white:
        return f"{user_id}_white"
    if device_slots == 3:
        return f"{user_id}_3"
    if device_slots == 10:
        return f"{user_id}_10"
    return str(user_id)


def panel_username_for_site_user(
    db_user_id: int,
    *,
    white: bool,
    device_slots: int = 5,
) -> str:
    """Username в панели для email-аккаунта (отрицательный user_id в БД)."""
    n = int(db_user_id)
    if n > 0:
        return panel_username(n, white=white, device_slots=device_slots)
    base = str(n)
    if len(base) < 3:
        base = f"n{n}"
    if white:
        return f"{base}_white"
    if device_slots == 3:
        return f"{base}_3"
    if device_slots == 10:
        return f"{base}_10"
    return base


def device_from_tariff_key(duration_key_plain: str) -> int:
    """Число устройств из ключа m{N}_d{D}; для legacy-ключей — DEFAULT_DEVICE_SLOTS."""
    m = re.fullmatch(r"m\d+_d(\d+)", duration_key_plain)
    if m:
        return int(m.group(1))
    return DEFAULT_DEVICE_SLOTS


def tariff_rub_and_desc(duration_key: str) -> Tuple[int, str]:
    return dct_price[duration_key], dct_desc[duration_key]


def tariff_days_for_x3(duration_key_plain: str) -> int:
    """
    Ключ без префикса white_ (уже отрезан при необходимости).
    Примеры: '3', '30', 'm1_d3'.
    """
    m_md = re.fullmatch(r"m(\d+)_d(\d+)", duration_key_plain)
    if m_md:
        months = int(m_md.group(1))
        return _MONTHS_TO_DAYS.get(months, 30 * months)
    return int(duration_key_plain)
