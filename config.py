from dotenv import load_dotenv
import os
from typing import List, Set, Optional

# Загрузка переменных окружения из .env файла
load_dotenv()

TG_TOKEN: Optional[str] = os.environ.get("TG_TOKEN")
ADMIN_IDS: Set[int] = {int(x) for x in os.environ.get("ADMIN_IDS", "").split(', ')} if os.environ.get("ADMIN_IDS") else set()
_cid = os.environ.get("CHECKER_ID")
CHECKER_ID: Optional[int] = int(_cid) if _cid else None
PLATEGA_API_KEY: Optional[str] = os.environ.get("PLATEGA_API_KEY")
PLATEGA_MERCHANT_ID: Optional[str] = os.environ.get("PLATEGA_MERCHANT_ID")
CHANEL_ID: Optional[int] = int(os.environ.get("CHANEL_ID"))
CRYPTOBOT_API_TOKEN: Optional[str] = os.environ.get("CRYPTOBOT_API_TOKEN")
PANEL_URL: Optional[str] = os.environ.get("PANEL_URL")
PANEL_API_TOKEN: Optional[str] = os.environ.get("PANEL_API_TOKEN")
BOT_URL: Optional[str] = os.environ.get("BOT_URL")
CHANEL_URL: Optional[str] = os.environ.get("CHANEL_URL")
SUPPORT_URL: Optional[str] = os.environ.get("SUPPORT_URL")
DOCUMENT_URL_1: Optional[str] = os.environ.get("DOCUMENT_URL_1")
DOCUMENT_URL_2: Optional[str] = os.environ.get("DOCUMENT_URL_2")
DOCUMENT_URL_3: Optional[str] = os.environ.get("DOCUMENT_URL_3")
TRUE_SUB_LINK: Optional[str] = os.environ.get("TRUE_SUB_LINK")
MIRROR_SUB_LINK: Optional[str] = os.environ.get("MIRROR_SUB_LINK")
SHORT_UUID_SECRET: Optional[str] = os.environ.get("SHORT_UUID_SECRET")

# WATA H2H: боевой https://api.wata.pro/api/h2h — песочница https://api-sandbox.wata.pro/api/h2h
WATA_API_BASE: str = os.environ.get("WATA_API_BASE", "https://api.wata.pro/api/h2h").rstrip("/")
WATA_API_CARD_KEY: Optional[str] = os.environ.get("WATA_API_CARD_KEY")
WATA_API_SBP_KEY: Optional[str] = os.environ.get("WATA_API_SBP_KEY")

API_FREEKASSA: Optional[str] = (os.environ.get("API_FREEKASSA") or "").strip() or None
SHOP_ID_FREEKASSA: Optional[int] = (
    int(os.environ["SHOP_ID_FREEKASSA"]) if os.environ.get("SHOP_ID_FREEKASSA") else None
)
FREEKASSA_SERVER_IP: str = os.environ.get("FREEKASSA_SERVER_IP", "127.0.0.1")

# Lead Tracker (POST /users/, /users/trial, /users/connected, /payments/)
LEAD_TRACKER_BASE: Optional[str] = (os.environ.get("LEAD_TRACKER_BASE") or "").strip() or None
LEAD_TRACKER_API_KEY: Optional[str] = (os.environ.get("LEAD_TRACKER_API_KEY") or "").strip() or None
LEAD_TRACKER_STAR_RUB_PER_STAR: str = os.environ.get("LEAD_TRACKER_STAR_RUB_PER_STAR", "1.0")

# HTTP API подписной страницы (web_api.py, старт из main). Заголовок: X-API-Key
SUB_PAGE_API_KEY: Optional[str] = (os.environ.get("SUB_PAGE_API_KEY") or "").strip() or None
# CORS для fetch со страницы подписки (через запятую). Пусто — разрешить любой origin (*).
_raw_cors = (os.environ.get("SUB_PAGE_CORS_ORIGINS") or "").strip()
SUB_PAGE_CORS_ORIGINS: List[str] = (
    [o.strip() for o in _raw_cors.split(",") if o.strip()] if _raw_cors else ["*"]
)
try:
    WEB_API_PORT: int = int((os.environ.get("WEB_API_PORT") or "8080").strip())
except ValueError:
    WEB_API_PORT = 8080
# ЮKassa (рекуррент): shopId и секретный ключ из личного кабинета; return_url — HTTPS после оплаты (по умолчанию BOT_URL).
YOUKASSA_SHOP_ID: Optional[str] = (os.environ.get("YOUKASSA_SHOP_ID") or "").strip() or None
YOUKASSA_API_KEY: Optional[str] = (os.environ.get("YOUKASSA_API_KEY") or "").strip() or None
YOUKASSA_RETURN_URL: Optional[str] = (os.environ.get("YOUKASSA_RETURN_URL") or "").strip() or None
# Чек 54-ФЗ: запасной email, если telegram user_id неизвестен (обычно {id}@telegram.org).
YOUKASSA_RECEIPT_EMAIL: str = (os.environ.get("YOUKASSA_RECEIPT_EMAIL") or "receipt@open21.top").strip()
# vat_code: 1 — без НДС; см. https://yookassa.ru/developers/payment-acceptance/receipts/54fz/yoomoney/parameters-values
YOUKASSA_VAT_CODE: int = int((os.environ.get("YOUKASSA_VAT_CODE") or "1").strip())
_ts = (os.environ.get("YOUKASSA_TAX_SYSTEM_CODE") or "").strip()
YOUKASSA_TAX_SYSTEM_CODE: Optional[int] = int(_ts) if _ts.isdigit() else None

# Web API (web_api.py): сайт + страница подписки + uvicorn в main
PUBLIC_SITE_URL: str = (os.environ.get("PUBLIC_SITE_URL") or "").strip().rstrip("/")
JWT_SECRET: Optional[str] = (os.environ.get("JWT_SECRET") or "").strip() or None
GOOGLE_CLIENT_ID: Optional[str] = (os.environ.get("GOOGLE_CLIENT_ID") or "").strip() or None
PAYMENT_MAX_PENDING_PER_USER: int = int((os.environ.get("PAYMENT_MAX_PENDING_PER_USER") or "8").strip())
SMTP_HOST: Optional[str] = (os.environ.get("SMTP_HOST") or "").strip() or None
SMTP_PORT: int = int((os.environ.get("SMTP_PORT") or "587").strip())
SMTP_USER: Optional[str] = (os.environ.get("SMTP_USER") or "").strip() or None
SMTP_PASSWORD: Optional[str] = (os.environ.get("SMTP_PASSWORD") or "").strip() or None
SMTP_FROM: Optional[str] = (os.environ.get("SMTP_FROM") or "").strip() or None

# Партнёрская программа («Зарабатывай с нами»)
PARTNER_PROCENT: int = int(os.environ.get("PARTNER_PROCENT", "20"))
PARTNER_MIN: int = int(os.environ.get("PARTNER_MIN", "500"))
PARTNER_SUPPORT_URL: str = (
    os.environ.get("PARTNER_SUPPORT_URL") or os.environ.get("SUPPORT_URL") or ""
).strip()
