from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto

from bot import sql, x3
from keyboard import (
    keyboard_import_os,
    keyboard_import_app,
    keyboard_import_sub,
    keyboard_import_end,
    create_kb,
)
from lexicon import lexicon

router: Router = Router()

OS_CALLBACKS = {'import_android', 'import_ios', 'import_windows', 'import_macos'}

# Замените file_id на актуальные для этого бота (используйте хендлер /get_photo_id)
HAPP_PHOTOS = [
    'AgACAgIAAxkBAAIFZ2m7iaXV_lqo4Ff3a5Ssl2bAyEZHAAI5Fmsb8A3hSRS2AsL1nuYGAQADAgADeQADOgQ',
    'AgACAgIAAxkBAAIFaWm7ia_CcGuxAxpOKeXvCIN0UZ1OAAI6Fmsb8A3hSTI14Snmr6IAAQEAAwIAA3kAAzoE',
]

V2_PHOTOS = [
    'AgACAgIAAxkBAAIFa2m7ic49LjT9q4c5cryS96HHJU6PAAI7Fmsb8A3hSXwD-7nuGg0VAQADAgADeQADOgQ',
    'AgACAgIAAxkBAAIFbWm7idTPdzO7EAFtIX9Wy1-8siEBAAI8Fmsb8A3hSV3SZWOU8yNwAQADAgADeQADOgQ',
    'AgACAgIAAxkBAAIFb2m7ieSG8Zx44GH6CX6O8nyZW-nSAAI-Fmsb8A3hSa4CKxp_6jCTAQADAgADeQADOgQ',
]

OS_DISPLAY = {
    'android': '🤖 Android',
    'ios': '🍎 iOS',
    'windows': '🖥️ Windows',
    'macos': '🍏 MacOS',
}

APP_DISPLAY = {
    'happ': '⭐️ Happ',
    'v2': '📡 V2raytun',
}

IMPORT_URLS = {
    'android': {
        'happ': {
            'url_app': 'https://play.google.com/store/apps/details?id=com.happproxy',
            'url_import': 'happ://add/{sub_link}',
        },
        'v2': {
            'url_app': 'https://play.google.com/store/apps/details?id=com.v2raytun.android',
            'url_import': 'v2raytun://import/{sub_link}',
        },
    },
    'ios': {
        'happ': {
            'url_app': 'https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973',
            'url_import': 'happ://add/{sub_link}',
        },
        'v2': {
            'url_app': 'https://apps.apple.com/app/v2raytun/id6476628951',
            'url_import': 'v2raytun://import/{sub_link}',
        },
    },
    'windows': {
        'happ': {
            'url_app': 'https://github.com/Happ-proxy/happ-desktop/releases/latest/download/setup-Happ.x64.exe',
            'url_import': 'happ://add/{sub_link}',
        },
        'v2': {
            'url_app': 'https://v2raytun.com/',
            'url_import': 'v2raytun://import/{sub_link}',
        },
    },
    'macos': {
        'happ': {
            'url_app': 'https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973',
            'url_import': 'happ://add/{sub_link}',
        },
        'v2': {
            'url_app': 'https://apps.apple.com/ru/app/v2raytun/id6476628951',
            'url_import': 'v2raytun://import/{sub_link}',
        },
    },
}


@router.callback_query(F.data == 'import')
async def import_select_os(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        text=lexicon['import_start'],
        reply_markup=keyboard_import_os()
    )


@router.callback_query(F.data.in_(OS_CALLBACKS))
async def import_select_app(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        text=lexicon['import_select_app'],
        reply_markup=keyboard_import_app(callback.data)
    )


@router.callback_query(
    F.data.startswith('import_') &
    (F.data.endswith('_happ') | F.data.endswith('_v2'))
)
async def import_select_sub(callback: CallbackQuery):
    user_data = await sql.get_user(callback.from_user.id)
    has_casual = has_white = False
    if user_data and user_data[9]:   # casual_subscription_end_date
        has_casual = True
    if user_data and user_data[10]:  # white_subscription_end_date
        has_white = True

    if not has_casual and not has_white:
        await callback.answer()
        await callback.message.answer(
            text=lexicon['no_sub'],
            reply_markup=create_kb(1, back_to_main='🔙 Назад')
        )
        return

    await callback.answer()
    await callback.message.answer(
        text=lexicon['import_select_sub'],
        reply_markup=keyboard_import_sub(callback.data, has_casual, has_white)
    )


@router.callback_query(
    F.data.startswith('import_') &
    (F.data.endswith('_casual') | F.data.endswith('_white'))
)
async def import_end(callback: CallbackQuery):
    await callback.answer()
    user_id = str(callback.from_user.id)

    if callback.data.endswith('_white'):
        sub_url = await x3.sublink(user_id + '_white')
        label = '🔥 Включи мобильный'
    else:
        sub_url = await x3.sublink(user_id)
        label = '💫 VPN PRO'

    if not sub_url:
        await callback.message.answer(
            '❌ Не удалось получить ссылку. Обратитесь в поддержку.',
            reply_markup=create_kb(1, back_to_main='🔙 Назад')
        )
        return

    parts = callback.data.split('_')
    os_key = parts[1]
    app_key = parts[2]

    urls = IMPORT_URLS[os_key][app_key]
    url_app = urls['url_app']

    if app_key == 'happ':
        lexicon_key = 'import_end_happ'
        photos = HAPP_PHOTOS
    else:
        lexicon_key = 'import_end_v2'
        photos = V2_PHOTOS

    caption = lexicon[lexicon_key].format(
        os=OS_DISPLAY[os_key],
        app=APP_DISPLAY[app_key],
        label=label,
        url_app=url_app,
        url_import=sub_url,
    )

    media = [InputMediaPhoto(media=file_id) for file_id in photos]
    media[0] = InputMediaPhoto(media=photos[0], caption=caption, parse_mode='HTML')

    await callback.message.answer_media_group(media=media)
