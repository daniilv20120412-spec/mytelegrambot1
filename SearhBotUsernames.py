from flask import Flask
import threading
import os
import asyncio
import random
import string
import requests
import json
from datetime import datetime, timedelta
from telethon import TelegramClient, events, Button, errors
from telethon.errors import FloodWaitError

app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# ========== КОНФИГ ==========
API_ID = 33387804
API_HASH = '96a5dcb90f673eacb08d5c87bdd60540'
BOT_TOKEN = '8841315782:AAFfEUUFNOKl1PdgjbZuDpqrJUkep6-a1A8'
ADMIN_ID = 7408006155
BOT_USERNAME = 'Usernames2026searhbot'
CHANNEL_USERNAME = 'usernames2026searh'

DEMO_MODE = True  # Временно включим демо, чтобы протестировать поиск

LIMITS = {5: 10, 6: 50}
PREMIUM_PRICES = {1: 15, 10: 35, 15: 45, 30: 125}

# ========== ХРАНИЛИЩА ==========
user_settings = {}
user_favorites = {}
user_premium = {}
user_searches = {}
promocodes = {}
referrals = {}
used_promocodes = {}

DATA_FILE = 'bot_data.json'

def load_data():
    global user_settings, user_favorites, user_premium, user_searches, promocodes, referrals, used_promocodes
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            user_settings = data.get('settings', {})
            user_favorites = data.get('favorites', {})
            user_premium = data.get('premium', {})
            user_searches = data.get('searches', {})
            promocodes = data.get('promocodes', {})
            referrals = data.get('referrals', {})
            used_promocodes = data.get('used_promocodes', {})

def save_data():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'settings': user_settings,
            'favorites': user_favorites,
            'premium': user_premium,
            'searches': user_searches,
            'promocodes': promocodes,
            'referrals': referrals,
            'used_promocodes': used_promocodes
        }, f, ensure_ascii=False, indent=2)

load_data()

if os.path.exists('bot.session'):
    os.remove('bot.session')

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# ========== ТЕКСТЫ ==========
T = {
    'welcome': '🌸 Добро пожаловать, это бот для поиска крутых юзернеймов! 💎',
    'premium_status': '👑 Премиум: {status}',
    'premium_remaining': '⏳ Осталось: {time}',
    'limits': '📊 Лимиты поиска:\n🔹 5 букв: {searches_5}\n🔹 6 букв: {searches_6}',
    'choose_function': 'Выбери функцию:',
    'search': '🔍 Поиск',
    'favorites': '⭐ Избранное',
    'premium_shop': '💎 Премиум',
    'promocode': '🎟 Промокод',
    'settings': '⚙️ Настройки',
    'referral': '👥 Рефералы',
    'searching': '🔍 Ищу свободный юзернейм... Подождите секунду...',
    'found': '✅ Найден свободный юзернейм!\n\n@{username}\n\n📊 На фрагменте — {fragment}\n\n⭐ В избранном: {faved} ({count}/5)',
    'remaining': '📊 Осталось поисков: {remaining}',
    'no_free': '😔 Не удалось найти свободный юзернейм. Попробуйте изменить настройки.',
    'limit_reached': '⛔ Лимит поиска исчерпан!\n\nВы использовали все {limit} попыток для {length}-буквенных юзов.\n\n⏳ Восстановление через: {time}\n🕐 {reset_time}\n\n💎 Купите премиум для безлимитного поиска!',
    'add_fav': '⭐ Добавить в избранное',
    'remove_fav': '🗑 Убрать из избранного',
    'find_more': '🔄 Найти ещё',
    'favorites_title': '⭐ Твои сохранённые юзернеймы (макс 5):',
    'no_favorites': '⭐ В избранном пока пусто\n\nНайди крутой юз и сохрани его!',
    'settings_title': '⚙️ Настройки',
    'settings_length': '📏 Количество букв: {length}',
    'settings_digits': '🔢 Цифры: {digits}',
    'choose_length': '📏 Выберите количество букв:',
    'length_5': '5 букв',
    'length_6': '6 букв',
    'digits_on': 'Включить цифры',
    'digits_off': 'Выключить цифры',
    'back': '🔙 Назад',
    'main_menu': '🏠 Главная',
    'premium_title': '💎 Премиум магазин',
    'premium_active': '✅ Премиум активен',
    'premium_inactive': '❌ Премиум не активен',
    'premium_features': '🔥 Что даёт премиум:\n• ♾ Безлимитный поиск (5 и 6 букв)\n• 🚀 Приоритетная генерация\n• 🎁 Бонусные промокоды',
    'choose_days': 'Выберите срок:',
    'buy_premium': '📅 {days} дней — {price} ⭐',
    'confirm_payment': '💎 Оплата премиума\n\n📅 Срок: {days} дней\n💰 Цена: {price} ⭐\n\nНажмите кнопку ниже для оплаты:',
    'pay_stars': '⭐ Оплатить звёздами',
    'payment_success': '✅ Премиум активирован на {days} дней!\n\n⏳ Действует до: {expiry}\n\n🔓 Открыт безлимитный поиск!',
    'promo_title': '🎟 Промокоды\n\nВведите промокод в чат.\n\nПример: /promo ABC12345',
    'promo_success': '✅ Промокод активирован!\n\n🎁 Получен премиум на {days} дней!\n⏳ Действует до: {expiry}\n\n🔓 Теперь у вас безлимитный поиск!',
    'promo_invalid': '❌ Неверный промокод',
    'promo_used': '❌ Количество активаций промокода исчерпано.',
    'promo_already_used': '❌ Вы уже активировали этот промокод ранее.',
    'referral_title': '👥 Реферальная система',
    'referral_link': '🔗 Твоя реферальная ссылка:\nhttps://t.me/{bot}?start={ref_code}',
    'referral_stats': '📊 Приглашено: {count} человек',
    'referral_reward': '🎁 За 10 приглашённых — премиум на 1 день!\n🎁 За покупку премиума рефералом — +5 дней тебе!',
    'referral_joined': '👤 Пользователь @{username} присоединился по вашей ссылке!',
    'referral_reward_10': '🎉 Вы пригласили 10 человек! Получите премиум на 1 день!',
    'referral_reward_purchase': '🎉 Ваш реферал @{username} купил премиум! Вы получили +5 дней!',
    'faved_yes': '✅ Да',
    'faved_no': '❌ Нет',
    'digits_on_text': 'Включены ✅',
    'digits_off_text': 'Выключены ❌',
    'favorites_full': '⚠️ Максимум 5 юзов в избранном! Удалите лишние.',
    'no_referrals': '👥 У вас пока нет рефералов.\n\nПриглашайте друзей и получайте бонусы!',
    'referral_code': '🔑 Ваш реферальный код: {code}',
    'set_lang': '🌐 Язык установлен: русский',
    'premium_already': '✅ У вас уже есть премиум!',
    'friends': '👥 Друзья',
    'referral_friends': '👥 Список приглашённых:',
    'no_referral_friends': 'Пока никого не пригласили',
    'fragment_detected': 'обнаружен ✅',
    'fragment_not_detected': 'не обнаружен ❌',
    'fragment_error': 'не удалось проверить ⚠️',
    'subscribe_required': f'🔥 Чтобы пользоваться ботом, подпишись на наш канал:\n👉 https://t.me/{CHANNEL_USERNAME}\n\nПосле подписки нажми кнопку "Проверить ✅"',
    'check_subscription': 'Проверить ✅',
    'subscription_success': '✅ Спасибо за подписку! Теперь вы можете пользоваться ботом.',
    'subscription_failed': '❌ Вы ещё не подписались на канал. Пожалуйста, подпишитесь и нажмите кнопку снова.',
    'payment_error': '⚠️ Реальная оплата звёздами пока в разработке. Свяжитесь с администратором.'
}

def txt(user_id, key, **kwargs):
    return T.get(key, key).format(**kwargs) if kwargs else T.get(key, key)

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def has_premium(user_id):
    if user_id not in user_premium:
        return False
    expiry = user_premium[user_id].get('expires')
    if not expiry:
        return False
    expiry_date = datetime.strptime(expiry, '%Y-%m-%d %H:%M:%S')
    if datetime.now() > expiry_date:
        user_premium[user_id]['active'] = False
        save_data()
        return False
    return True

def get_premium_remaining(user_id):
    if user_id not in user_premium:
        return None
    expiry = user_premium[user_id].get('expires')
    if not expiry:
        return None
    expiry_date = datetime.strptime(expiry, '%Y-%m-%d %H:%M:%S')
    remaining = expiry_date - datetime.now()
    if remaining.total_seconds() < 0:
        return None
    days = remaining.days
    hours = remaining.seconds // 3600
    minutes = (remaining.seconds % 3600) // 60
    return f"{days}д {hours}ч {minutes}м"

def add_premium(user_id, days):
    expiry_date = datetime.now() + timedelta(days=days)
    user_premium[user_id] = {
        'expires': expiry_date.strftime('%Y-%m-%d %H:%M:%S'),
        'active': True
    }
    save_data()

def check_limit(user_id, length):
    if has_premium(user_id):
        return True, '♾ Безлимит', None
    if user_id not in user_searches:
        user_searches[user_id] = {'5': {'count': 0, 'reset_time': None}, '6': {'count': 0, 'reset_time': None}}
        save_data()
    key = str(length)
    if key not in user_searches[user_id]:
        user_searches[user_id][key] = {'count': 0, 'reset_time': None}
        save_data()
    data = user_searches[user_id][key]
    reset_time_str = data.get('reset_time')
    if reset_time_str:
        reset_dt = datetime.strptime(reset_time_str, '%Y-%m-%d %H:%M:%S')
        if datetime.now() >= reset_dt:
            data['count'] = 0
            data['reset_time'] = None
            save_data()
            return True, LIMITS[length], None
        else:
            remaining = reset_dt - datetime.now()
            return False, 0, remaining
    used = data.get('count', 0)
    limit = LIMITS[length]
    if used < limit:
        return True, limit - used, None
    else:
        reset_dt = datetime.now() + timedelta(hours=24)
        data['reset_time'] = reset_dt.strftime('%Y-%m-%d %H:%M:%S')
        save_data()
        remaining = reset_dt - datetime.now()
        return False, 0, remaining

def increment_search(user_id, length):
    if user_id not in user_searches:
        user_searches[user_id] = {'5': {'count': 0, 'reset_time': None}, '6': {'count': 0, 'reset_time': None}}
    key = str(length)
    if key not in user_searches[user_id]:
        user_searches[user_id][key] = {'count': 0, 'reset_time': None}
    data = user_searches[user_id][key]
    reset_time_str = data.get('reset_time')
    if reset_time_str:
        reset_dt = datetime.strptime(reset_time_str, '%Y-%m-%d %H:%M:%S')
        if datetime.now() >= reset_dt:
            data['count'] = 0
            data['reset_time'] = None
    data['count'] += 1
    if data['count'] >= LIMITS[length] and not data.get('reset_time'):
        reset_dt = datetime.now() + timedelta(hours=24)
        data['reset_time'] = reset_dt.strftime('%Y-%m-%d %H:%M:%S')
    save_data()

def get_remaining(user_id, length):
    can, rem, extra = check_limit(user_id, length)
    if can:
        return str(rem), None
    else:
        if extra:
            hours = extra.seconds // 3600
            minutes = (extra.seconds % 3600) // 60
            return f'⏳ 0 (через {hours}ч {minutes}м)', extra
        else:
            return '⏳ 0', None

def format_time(td):
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    return f"{hours}ч {minutes}м"

def generate_username(length, with_digits=False):
    chars = string.ascii_lowercase
    if with_digits:
        chars += string.digits
    first = random.choice(string.ascii_lowercase)
    rest = ''.join(random.choices(chars, k=length-1))
    return first + rest

# ========== НОВАЯ ФУНКЦИЯ ПРОВЕРКИ ЧЕРЕЗ TELEGRAM API ==========
async def is_username_free(username):
    """Проверяет, свободен ли юзернейм через Telegram API"""
    try:
        # Пробуем получить информацию о пользователе
        await bot.get_entity(f'@{username}')
        return False  # Если получили — значит занят
    except FloodWaitError as e:
        # Если Telegram говорит ждать — ждём и пробуем ещё раз
        await asyncio.sleep(e.seconds)
        return None
    except ValueError:
        # Если ValueError — значит юзернейм свободен
        return True
    except Exception as e:
        # Если другая ошибка — считаем, что юзернейм занят (чтобы не спамить)
        print(f"Ошибка проверки @{username}: {e}")
        return False

def check_fragment(username):
    try:
        url = f'https://fragment.com/username/{username}'
        response = requests.get(url, timeout=5)
        return 'fragment_detected' if response.status_code == 200 else 'fragment_not_detected'
    except:
        return 'fragment_error'

async def is_subscribed(user_id):
    try:
        channel = await bot.get_entity(f'@{CHANNEL_USERNAME}')
        await bot.get_permissions(channel, user_id)
        return True
    except errors.rpcerrorlist.UserNotParticipantError:
        return False
    except:
        return True

def generate_ref_code(user_id):
    return f"{user_id}{random.randint(100, 999)}"

# ========== ОБРАБОТЧИКИ ==========
@bot.on(events.NewMessage(pattern='/start(?: (.*))?'))
async def start(event):
    user_id = event.sender_id
    args = event.pattern_match.group(1)
    if args and args.isdigit():
        referrer_id = int(args)
        if referrer_id != user_id:
            if user_id not in referrals:
                referrals[user_id] = {'invited': [], 'invited_by': referrer_id}
            elif referrals[user_id].get('invited_by') is None:
                referrals[user_id]['invited_by'] = referrer_id
            if referrer_id not in referrals:
                referrals[referrer_id] = {'invited': [], 'invited_by': None}
            if user_id not in referrals[referrer_id]['invited']:
                referrals[referrer_id]['invited'].append(user_id)
                save_data()
                if len(referrals[referrer_id]['invited']) >= 10:
                    add_premium(referrer_id, 1)
                    try:
                        await bot.send_message(referrer_id, txt(referrer_id, 'referral_reward_10'))
                    except:
                        pass
                try:
                    username = event.sender.username or str(user_id)
                    await bot.send_message(referrer_id, txt(referrer_id, 'referral_joined', username=username))
                except:
                    pass
    if user_id not in user_settings:
        user_settings[user_id] = {'length': 5, 'digits': False}
        save_data()
    if user_id not in user_favorites:
        user_favorites[user_id] = []
        save_data()
    if user_id not in referrals:
        referrals[user_id] = {'invited': [], 'invited_by': None}
        save_data()

    if await is_subscribed(user_id):
        await send_main_menu(event, user_id, edit=False)
    else:
        text = txt(user_id, 'subscribe_required')
        buttons = [[Button.inline(txt(user_id, 'check_subscription'), b'check_sub')]]
        await event.respond(text, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'check_sub'))
async def check_sub(event):
    user_id = event.sender_id
    if await is_subscribed(user_id):
        await event.edit(txt(user_id, 'subscription_success'))
        await send_main_menu(event, user_id, edit=False)
    else:
        await event.answer(txt(user_id, 'subscription_failed'), alert=True)

async def send_main_menu(event, user_id, edit=True):
    premium_status = '✅ Активен' if has_premium(user_id) else '❌ Не активен'
    remaining_rem = get_premium_remaining(user_id) if has_premium(user_id) else None
    searches_5, _ = get_remaining(user_id, 5)
    searches_6, _ = get_remaining(user_id, 6)
    text = (txt(user_id, 'welcome') + '\n\n' +
            txt(user_id, 'premium_status', status=premium_status) +
            (('\n' + txt(user_id, 'premium_remaining', time=remaining_rem)) if remaining_rem else '') +
            '\n\n' + txt(user_id, 'limits', searches_5=str(searches_5), searches_6=str(searches_6)) +
            '\n\n' + txt(user_id, 'choose_function'))
    buttons = [
        [Button.inline(txt(user_id, 'search'), b'search')],
        [Button.inline(txt(user_id, 'favorites'), b'favorites')],
        [Button.inline(txt(user_id, 'premium_shop'), b'premium_shop')],
        [Button.inline(txt(user_id, 'promocode'), b'promocode_menu')],
        [Button.inline(txt(user_id, 'settings'), b'settings')],
        [Button.inline(txt(user_id, 'referral'), b'referral')]
    ]
    if edit:
        await event.edit(text, buttons=buttons)
    else:
        await event.respond(text, buttons=buttons)

# ========== ГЛАВНЫЙ ОБРАБОТЧИК ПОИСКА ==========
@bot.on(events.CallbackQuery(data=b'search'))
async def search_callback(event):
    user_id = event.sender_id
    settings = user_settings.get(user_id, {'length': 5, 'digits': False})
    length = settings['length']
    digits = settings['digits']

    can, remaining, remaining_time = check_limit(user_id, length)
    if not can:
        reset_time_str = user_searches.get(user_id, {}).get(str(length), {}).get('reset_time')
        reset_dt = datetime.strptime(reset_time_str, '%Y-%m-%d %H:%M:%S') if reset_time_str else None
        if reset_dt:
            time_left = format_time(reset_dt - datetime.now())
            reset_formatted = reset_dt.strftime('%d.%m.%Y %H:%M')
            text = txt(user_id, 'limit_reached', limit=LIMITS[length], length=length,
                       time=time_left, reset_time=reset_formatted)
        else:
            text = txt(user_id, 'limit_reached', limit=LIMITS[length], length=length,
                       time='24ч', reset_time='')
        buttons = [
            [Button.inline(txt(user_id, 'premium_shop'), b'premium_shop')],
            [Button.inline(txt(user_id, 'main_menu'), b'main_menu')]
        ]
        await event.edit(text, buttons=buttons)
        return

    await event.edit(txt(user_id, 'searching'))

    found = None
    for _ in range(30):  # 30 попыток, чтобы не перегружать API
        username = generate_username(length, digits)
        free = await is_username_free(username)
        if free is True:
            found = username
            break
        elif free is None:
            # Если был FloodWaitError — ждём и продолжаем
            continue
        await asyncio.sleep(0.5)  # Задержка между запросами

    increment_search(user_id, length)

    if found:
        fragment_status = check_fragment(found)
        fragment_key = 'fragment_detected' if 'fragment_detected' in fragment_status else 'fragment_not_detected' if 'fragment_not_detected' in fragment_status else 'fragment_error'
        fragment_display = txt(user_id, fragment_key)
        fav_list = user_favorites.get(user_id, [])
        is_faved = found in fav_list
        remaining, _ = get_remaining(user_id, length)

        text = txt(user_id, 'found',
                   username=found,
                   fragment=fragment_display,
                   faved=txt(user_id, 'faved_yes') if is_faved else txt(user_id, 'faved_no'),
                   count=len(fav_list))
        text += '\n\n' + txt(user_id, 'remaining', remaining=str(remaining))

        buttons = []
        if is_faved:
            buttons.append([Button.inline(txt(user_id, 'remove_fav'), f'remove_fav_{found}'.encode())])
        else:
            if len(fav_list) < 5:
                buttons.append([Button.inline(txt(user_id, 'add_fav'), f'add_fav_{found}'.encode())])
            else:
                buttons.append([Button.inline(txt(user_id, 'favorites_full'), b'favorites_full')])
        buttons.append([Button.inline(txt(user_id, 'find_more'), b'search')])
        buttons.append([Button.inline(txt(user_id, 'favorites'), b'favorites')])
        buttons.append([Button.inline(txt(user_id, 'main_menu'), b'main_menu')])
        await event.edit(text, buttons=buttons)
    else:
        await event.edit(txt(user_id, 'no_free'),
                         buttons=[[Button.inline(txt(user_id, 'settings'), b'settings')]])

# ========== ОСТАЛЬНЫЕ КНОПКИ ==========
@bot.on(events.CallbackQuery)
async def callback(event):
    user_id = event.sender_id
    data = event.data.decode()

    if data == 'main_menu':
        await send_main_menu(event, user_id)
        return

    if data == 'favorites':
        fav_list = user_favorites.get(user_id, [])
        if not fav_list:
            await event.edit(txt(user_id, 'no_favorites'),
                             buttons=[[Button.inline(txt(user_id, 'search'), b'search')],
                                      [Button.inline(txt(user_id, 'main_menu'), b'main_menu')]])
            return
        text = txt(user_id, 'favorites_title') + '\n\n'
        for i, username in enumerate(fav_list, 1):
            free = await is_username_free(username)
            status = '🟢 Свободен' if free else '🔴 Занят'
            fragment_status = check_fragment(username)
            fragment_key = 'fragment_detected' if 'fragment_detected' in fragment_status else 'fragment_not_detected' if 'fragment_not_detected' in fragment_status else 'fragment_error'
            fragment_display = txt(user_id, fragment_key)
            text += f"{i}. @{username} — {status} | Fragment: {fragment_display}\n"
        buttons = []
        for username in fav_list:
            buttons.append([Button.inline(f'🗑 Delete @{username}', f'remove_fav_from_list_{username}'.encode())])
        buttons.append([Button.inline(txt(user_id, 'search'), b'search')])
        buttons.append([Button.inline(txt(user_id, 'main_menu'), b'main_menu')])
        await event.edit(text, buttons=buttons)
        return

    if data == 'premium_shop':
        has_prem = has_premium(user_id)
        remaining = get_premium_remaining(user_id) if has_prem else None
        text = txt(user_id, 'premium_title') + '\n\n'
        text += txt(user_id, 'premium_active') if has_prem else txt(user_id, 'premium_inactive')
        if remaining:
            text += '\n⏳ ' + txt(user_id, 'premium_remaining', time=remaining)
        text += '\n\n' + txt(user_id, 'premium_features') + '\n\n'
        text += txt(user_id, 'choose_days')
        buttons = []
        for days in sorted(PREMIUM_PRICES.keys()):
            price = PREMIUM_PRICES[days]
            buttons.append([Button.inline(txt(user_id, 'buy_premium', days=days, price=price),
                                          f'buy_premium_{days}'.encode())])
        buttons.append([Button.inline(txt(user_id, 'main_menu'), b'main_menu')])
        await event.edit(text, buttons=buttons)
        return

    if data == 'promocode_menu':
        await event.edit(txt(user_id, 'promo_title'),
                         buttons=[[Button.inline(txt(user_id, 'back'), b'main_menu')]])
        return

    if data == 'referral':
        ref_data = referrals.get(user_id, {'invited': [], 'invited_by': None})
        invited_count = len(ref_data.get('invited', []))
        ref_code = generate_ref_code(user_id)
        text = (txt(user_id, 'referral_title') + '\n\n' +
                txt(user_id, 'referral_link', bot=BOT_USERNAME, ref_code=ref_code) + '\n\n' +
                txt(user_id, 'referral_code', code=ref_code) + '\n\n' +
                txt(user_id, 'referral_stats', count=invited_count) + '\n\n' +
                txt(user_id, 'referral_reward'))
        buttons = [
            [Button.inline(txt(user_id, 'friends'), b'referral_friends')],
            [Button.inline(txt(user_id, 'main_menu'), b'main_menu')]
        ]
        await event.edit(text, buttons=buttons)
        return

    if data == 'referral_friends':
        invited = referrals.get(user_id, {}).get('invited', [])
        text = txt(user_id, 'referral_friends') + '\n\n'
        if not invited:
            text += txt(user_id, 'no_referral_friends')
        else:
            for i, friend_id in enumerate(invited, 1):
                try:
                    user = await bot.get_entity(friend_id)
                    name = user.username or user.first_name or str(friend_id)
                    text += f"{i}. @{name}\n"
                except:
                    text += f"{i}. {friend_id}\n"
        buttons = [[Button.inline(txt(user_id, 'back'), b'referral')]]
        await event.edit(text, buttons=buttons)
        return

    if data == 'settings':
        settings = user_settings.get(user_id, {'length': 5, 'digits': False})
        length = settings['length']
        digits = settings['digits']
        text = (txt(user_id, 'settings_title') + '\n\n' +
                txt(user_id, 'settings_length', length=length) + '\n' +
                txt(user_id, 'settings_digits',
                    digits=txt(user_id, 'digits_on_text') if digits else txt(user_id, 'digits_off_text')))
        buttons = [
            [Button.inline(txt(user_id, 'length_5') if length == 6 else txt(user_id, 'length_6'),
                           b'toggle_length')],
            [Button.inline(txt(user_id, 'digits_off') if digits else txt(user_id, 'digits_on'),
                           b'toggle_digits')],
            [Button.inline(txt(user_id, 'main_menu'), b'main_menu')]
        ]
        await event.edit(text, buttons=buttons)
        return

    if data == 'toggle_length':
        current = user_settings[user_id].get('length', 5)
        user_settings[user_id]['length'] = 6 if current == 5 else 5
        save_data()
        await event.edit(f'✅ Установлено: {user_settings[user_id]["length"]} букв',
                         buttons=[[Button.inline(txt(user_id, 'back'), b'settings')]])
        return

    if data == 'toggle_digits':
        user_settings[user_id]['digits'] = not user_settings[user_id].get('digits', False)
        save_data()
        await event.edit(f'✅ Цифры {"включены" if user_settings[user_id]["digits"] else "выключены"}',
                         buttons=[[Button.inline(txt(user_id, 'back'), b'settings')]])
        return

    if data.startswith('add_fav_'):
        username = data.replace('add_fav_', '')
        fav_list = user_favorites.get(user_id, [])
        if username not in fav_list and len(fav_list) < 5:
            fav_list.append(username)
            user_favorites[user_id] = fav_list
            save_data()
            await event.answer(f'⭐ {username} добавлен!', alert=True)
        # обновляем результат поиска
        fragment_status = check_fragment(username)
        fragment_key = 'fragment_detected' if 'fragment_detected' in fragment_status else 'fragment_not_detected' if 'fragment_not_detected' in fragment_status else 'fragment_error'
        fragment_display = txt(user_id, fragment_key)
        is_faved = username in fav_list
        remaining, _ = get_remaining(user_id, len(username))
        text = txt(user_id, 'found', username=username, fragment=fragment_display,
                   faved=txt(user_id, 'faved_yes') if is_faved else txt(user_id, 'faved_no'),
                   count=len(fav_list))
        text += '\n\n' + txt(user_id, 'remaining', remaining=str(remaining))
        buttons = []
        if is_faved:
            buttons.append([Button.inline(txt(user_id, 'remove_fav'), f'remove_fav_{username}'.encode())])
        else:
            if len(fav_list) < 5:
                buttons.append([Button.inline(txt(user_id, 'add_fav'), f'add_fav_{username}'.encode())])
            else:
                buttons.append([Button.inline(txt(user_id, 'favorites_full'), b'favorites_full')])
        buttons.append([Button.inline(txt(user_id, 'find_more'), b'search')])
        buttons.append([Button.inline(txt(user_id, 'favorites'), b'favorites')])
        buttons.append([Button.inline(txt(user_id, 'main_menu'), b'main_menu')])
        await event.edit(text, buttons=buttons)
        return

    if data.startswith('remove_fav_'):
        username = data.replace('remove_fav_', '')
        fav_list = user_favorites.get(user_id, [])
        if username in fav_list:
            fav_list.remove(username)
            user_favorites[user_id] = fav_list
            save_data()
            await event.answer(f'🗑 {username} удалён!', alert=True)
        # обновляем результат поиска
        fragment_status = check_fragment(username)
        fragment_key = 'fragment_detected' if 'fragment_detected' in fragment_status else 'fragment_not_detected' if 'fragment_not_detected' in fragment_status else 'fragment_error'
        fragment_display = txt(user_id, fragment_key)
        is_faved = username in fav_list
        remaining, _ = get_remaining(user_id, len(username))
        text = txt(user_id, 'found', username=username, fragment=fragment_display,
                   faved=txt(user_id, 'faved_yes') if is_faved else txt(user_id, 'faved_no'),
                   count=len(fav_list))
        text += '\n\n' + txt(user_id, 'remaining', remaining=str(remaining))
        buttons = []
        if is_faved:
            buttons.append([Button.inline(txt(user_id, 'remove_fav'), f'remove_fav_{username}'.encode())])
        else:
            if len(fav_list) < 5:
                buttons.append([Button.inline(txt(user_id, 'add_fav'), f'add_fav_{username}'.encode())])
            else:
                buttons.append([Button.inline(txt(user_id, 'favorites_full'), b'favorites_full')])
        buttons.append([Button.inline(txt(user_id, 'find_more'), b'search')])
        buttons.append([Button.inline(txt(user_id, 'favorites'), b'favorites')])
        buttons.append([Button.inline(txt(user_id, 'main_menu'), b'main_menu')])
        await event.edit(text, buttons=buttons)
        return

    if data.startswith('remove_fav_from_list_'):
        username = data.replace('remove_fav_from_list_', '')
        fav_list = user_favorites.get(user_id, [])
        if username in fav_list:
            fav_list.remove(username)
            user_favorites[user_id] = fav_list
            save_data()
            await event.answer(f'🗑 {username} удалён!', alert=True)
        fav_list = user_favorites.get(user_id, [])
        if not fav_list:
            await event.edit(txt(user_id, 'no_favorites'),
                             buttons=[[Button.inline(txt(user_id, 'search'), b'search')],
                                      [Button.inline(txt(user_id, 'main_menu'), b'main_menu')]])
            return
        text = txt(user_id, 'favorites_title') + '\n\n'
        for i, uname in enumerate(fav_list, 1):
            free = await is_username_free(uname)
            status = '🟢 Свободен' if free else '🔴 Занят'
            fragment_status = check_fragment(uname)
            fragment_key = 'fragment_detected' if 'fragment_detected' in fragment_status else 'fragment_not_detected' if 'fragment_not_detected' in fragment_status else 'fragment_error'
            fragment_display = txt(user_id, fragment_key)
            text += f"{i}. @{uname} — {status} | Fragment: {fragment_display}\n"
        buttons = []
        for uname in fav_list:
            buttons.append([Button.inline(f'🗑 Delete @{uname}', f'remove_fav_from_list_{uname}'.encode())])
        buttons.append([Button.inline(txt(user_id, 'search'), b'search')])
        buttons.append([Button.inline(txt(user_id, 'main_menu'), b'main_menu')])
        await event.edit(text, buttons=buttons)
        return

    if data.startswith('buy_premium_'):
        days = int(data.replace('buy_premium_', ''))
        price = PREMIUM_PRICES.get(days)
        if not price:
            await event.answer('❌ Неверный срок!', alert=True)
            return
        text = txt(user_id, 'confirm_payment', days=days, price=price)
        buttons = [
            [Button.inline(txt(user_id, 'pay_stars'), f'pay_stars_{days}'.encode())],
            [Button.inline(txt(user_id, 'back'), b'premium_shop')]
        ]
        await event.edit(text, buttons=buttons)
        return

    if data.startswith('pay_stars_'):
        days = int(data.replace('pay_stars_', ''))
        if has_premium(user_id):
            await event.answer(txt(user_id, 'premium_already'), alert=True)
            return
        # ДЕМО-РЕЖИМ (для теста премиум активируется бесплатно)
        add_premium(user_id, days)
        expiry_date = datetime.now() + timedelta(days=days)
        await event.edit(txt(user_id, 'payment_success', days=days,
                             expiry=expiry_date.strftime('%d.%m.%Y %H:%M')),
                         buttons=[[Button.inline(txt(user_id, 'search'), b'search')],
                                  [Button.inline(txt(user_id, 'main_menu'), b'main_menu')]])
        return

    if data == 'favorites_full':
        await event.answer(txt(user_id, 'favorites_full'), alert=True)
        return

# ========== ПРОМОКОДЫ ==========
@bot.on(events.NewMessage(pattern='/promo .+'))
async def handle_promo(event):
    user_id = event.sender_id
    code = event.raw_text.replace('/promo', '').strip().upper()
    if code not in promocodes:
        await event.reply(txt(user_id, 'promo_invalid'))
        return
    promo = promocodes[code]
    if promo['used'] >= promo['activations']:
        await event.reply(txt(user_id, 'promo_used'))
        return
    if user_id in used_promocodes and code in used_promocodes[user_id]:
        await event.reply(txt(user_id, 'promo_already_used'))
        return
    promo['used'] += 1
    reward = promo['reward']
    days_map = {'premium_1': 1, 'premium_10': 10, 'premium_15': 15, 'premium_30': 30}
    days = days_map.get(reward, 1)
    add_premium(user_id, days)
    if user_id not in used_promocodes:
        used_promocodes[user_id] = []
    used_promocodes[user_id].append(code)
    save_data()
    expiry_date = datetime.now() + timedelta(days=days)
    await event.reply(txt(user_id, 'promo_success', days=days,
                          expiry=expiry_date.strftime('%d.%m.%Y %H:%M')))

@bot.on(events.NewMessage(pattern='/create_promo .+ .+'))
async def create_promo(event):
    if event.sender_id != ADMIN_ID:
        await event.reply('⛔ Доступ запрещён')
        return
    parts = event.raw_text.split()
    try:
        activations = int(parts[1])
        reward = parts[2]
        if reward not in ['premium_1', 'premium_10', 'premium_15', 'premium_30']:
            await event.reply('❌ Награда должна быть: premium_1, premium_10, premium_15, premium_30')
            return
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        promocodes[code] = {'activations': activations, 'used': 0, 'reward': reward}
        save_data()
        await event.reply(f"✅ Промокод создан!\n\n🎟 Код: `{code}`\n📊 Активаций: {activations}\n🎁 Награда: {reward}\n\nИспользуйте: /promo {code}")
    except:
        await event.reply('❌ Формат: /create_promo [кол-во_активаций] [награда]\nНаграды: premium_1, premium_10, premium_15, premium_30')

# ========== ЗАПУСК ==========
print('🤖 Бот запущен!')
print(f'Канал для подписки: @{CHANNEL_USERNAME}')
print('Лимиты: 5 букв — 10/день, 6 букв — 50/день (сброс через 24 часа)')
print('Для создания промокода: /create_promo 5 premium_30')
print(f'Демо-режим: {"ВКЛЮЧЕН" if DEMO_MODE else "ВЫКЛЮЧЕН"}')

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()
bot.run_until_disconnected()
