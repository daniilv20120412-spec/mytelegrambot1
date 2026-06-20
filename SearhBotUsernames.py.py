import asyncio
import random
import string
import requests
import json
import os
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

# ========== КОНФИГ ==========
API_ID = 33387804
API_HASH = '96a5dcb90f673eacb08d5c87bdd60540'
BOT_TOKEN = '8841315782:AAFfEUUFNOKl1PdgjbZuDpqrJUkep6-a1A8'
ADMIN_ID = 7408006155  # Ваш Telegram ID
BOT_USERNAME = 'Usernames2026searhbot'  # БЕЗ @, например: username_bot

# ========== ЛИМИТЫ ==========
LIMITS = {
    5: 10,   # 5 букв — 10 поисков
    6: 50    # 6 букв — 50 поисков
}

# ========== ЦЕНЫ ПРЕМИУМА ==========
PREMIUM_PRICES = {
    1: 15,
    10: 35,
    15: 45,
    30: 125
}

# ========== ХРАНИЛИЩА ==========
user_settings = {}        # {user_id: {'length': 5, 'digits': False, 'lang': 'ru'}}
user_favorites = {}       # {user_id: ['username1', ...]}
user_premium = {}         # {user_id: {'expires': '2026-07-01 12:00:00', 'active': True}}
user_searches = {}        # {user_id: {'5': {'count': 0, 'reset_time': None}, '6': {...}}}
promocodes = {}           # {code: {'activations': 5, 'used': 0, 'reward': 'premium_30'}}
referrals = {}            # {user_id: {'invited': [user_id1, user_id2], 'invited_by': user_id}}
pending_payments = {}     # {user_id: {'days': 1, 'price': 15}}

# ========== ФАЙЛ ДЛЯ СОХРАНЕНИЯ ==========
DATA_FILE = 'bot_data.json'

def load_data():
    global user_settings, user_favorites, user_premium, user_searches, promocodes, referrals
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            user_settings = data.get('settings', {})
            user_favorites = data.get('favorites', {})
            user_premium = data.get('premium', {})
            user_searches = data.get('searches', {})
            promocodes = data.get('promocodes', {})
            referrals = data.get('referrals', {})

def save_data():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'settings': user_settings,
            'favorites': user_favorites,
            'premium': user_premium,
            'searches': user_searches,
            'promocodes': promocodes,
            'referrals': referrals
        }, f, ensure_ascii=False, indent=2)

load_data()

# ========== ПОДКЛЮЧЕНИЕ ==========
bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# ========== ЯЗЫКИ ==========
TRANSLATIONS = {
    'ru': {
        'welcome': '🌸 Добро пожаловать, это бот для поиска крутых юзернеймов! 💎',
        'premium_status': '👑 Премиум: {status}',
        'premium_remaining': '⏳ Осталось: {time}',
        'limits': '📊 Лимиты поиска:\n🔹 5 букв: {searches_5}\n🔹 6 букв: {searches_6}',
        'choose_function': 'Выбери функцию:',
        'search': '1. Поиск 🔍',
        'favorites': '2. Избранное ⭐',
        'premium_shop': '3. Премиум 💎',
        'promocode': '4. Промокод 🎟',
        'settings': '5. Настройки ⚙️',
        'referral': '6. Рефералы 👥',
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
        'settings_lang': '🌐 Язык: {lang}',
        'choose_length': '📏 Выберите количество букв:',
        'length_5': '1. 5 букв',
        'length_6': '2. 6 букв',
        'digits_settings': '🔢 Настройка цифр:',
        'digits_on': '1. Включить цифры',
        'digits_off': '2. Выключить цифры',
        'lang_settings': '🌐 Выберите язык:',
        'lang_ru': '🇷🇺 Русский',
        'lang_en': '🇬🇧 English',
        'back': '🔙 Назад',
        'main_menu': '🏠 Главная',
        'premium_title': '💎 Премиум магазин',
        'premium_active': '✅ Премиум активен',
        'premium_inactive': '❌ Премиум не активен',
        'premium_features': '🔥 Что даёт премиум:\n• ♾ Безлимитный поиск (5 и 6 букв)\n• 🚀 Приоритетная генерация\n• 🎁 Бонусные промокоды',
        'choose_days': 'Выберите срок:',
        'buy_premium': '📅 {days} дней — {price} ⭐',
        'confirm_payment': '💎 Оплата премиума\n\n📅 Срок: {days} дней\n💰 Цена: {price} ⭐\n\nНажмите кнопку ниже для активации:',
        'pay_stars': '⭐ Активировать (демо)',
        'payment_success': '✅ Премиум активирован на {days} дней!\n\n⏳ Действует до: {expiry}\n\n🔓 Открыт безлимитный поиск!',
        'promo_title': '🎟 Промокоды\n\nВведите промокод в чат.\n\nПример: /promo ABC12345\n\nПромокод может давать:\n• Бесплатный премиум\n• Бонусные дни',
        'promo_success': '✅ Промокод активирован!\n\n🎁 Получен премиум на {days} дней!\n⏳ Действует до: {expiry}\n\n🔓 Теперь у вас безлимитный поиск!',
        'promo_invalid': '❌ Неверный промокод',
        'promo_used': '❌ Промокод уже использован максимальное число раз',
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
        'payment_cancelled': '❌ Оплата отменена',
        'payment_error': '❌ Ошибка оплаты. Попробуйте позже.',
        'no_referrals': '👥 У вас пока нет рефералов.\n\nПриглашайте друзей и получайте бонусы!',
        'referral_code': '🔑 Ваш реферальный код: {code}',
        'set_lang': '🌐 Язык установлен: {lang}',
        'premium_already': '✅ У вас уже есть премиум!',
        'not_enough_stars': '❌ Недостаточно звёзд! Нужно: {price} ⭐',
        'friends': '👥 Друзья',
        'info': 'ℹ️ Информация',
        'referral_friends': '👥 Список приглашённых:',
        'no_referral_friends': 'Пока никого не пригласили'
    },
    'en': {
        'welcome': '🌸 Welcome! This bot helps you find cool usernames! 💎',
        'premium_status': '👑 Premium: {status}',
        'premium_remaining': '⏳ Remaining: {time}',
        'limits': '📊 Search limits:\n🔹 5 letters: {searches_5}\n🔹 6 letters: {searches_6}',
        'choose_function': 'Choose a function:',
        'search': '1. Search 🔍',
        'favorites': '2. Favorites ⭐',
        'premium_shop': '3. Premium 💎',
        'promocode': '4. Promo code 🎟',
        'settings': '5. Settings ⚙️',
        'referral': '6. Referrals 👥',
        'searching': '🔍 Searching for a free username... Please wait...',
        'found': '✅ Free username found!\n\n@{username}\n\n📊 On Fragment — {fragment}\n\n⭐ In favorites: {faved} ({count}/5)',
        'remaining': '📊 Searches left: {remaining}',
        'no_free': '😔 Could not find a free username. Try changing settings.',
        'limit_reached': '⛔ Search limit reached!\n\nYou used all {limit} attempts for {length}-letter usernames.\n\n⏳ Reset in: {time}\n🕐 {reset_time}\n\n💎 Buy premium for unlimited search!',
        'add_fav': '⭐ Add to favorites',
        'remove_fav': '🗑 Remove from favorites',
        'find_more': '🔄 Find more',
        'favorites_title': '⭐ Your saved usernames (max 5):',
        'no_favorites': '⭐ No favorites yet\n\nFind a cool username and save it!',
        'settings_title': '⚙️ Settings',
        'settings_length': '📏 Letters count: {length}',
        'settings_digits': '🔢 Digits: {digits}',
        'settings_lang': '🌐 Language: {lang}',
        'choose_length': '📏 Choose letters count:',
        'length_5': '1. 5 letters',
        'length_6': '2. 6 letters',
        'digits_settings': '🔢 Digits settings:',
        'digits_on': '1. Enable digits',
        'digits_off': '2. Disable digits',
        'lang_settings': '🌐 Choose language:',
        'lang_ru': '🇷🇺 Russian',
        'lang_en': '🇬🇧 English',
        'back': '🔙 Back',
        'main_menu': '🏠 Main menu',
        'premium_title': '💎 Premium Shop',
        'premium_active': '✅ Premium active',
        'premium_inactive': '❌ Premium not active',
        'premium_features': '🔥 What premium gives:\n• ♾ Unlimited search (5 and 6 letters)\n• 🚀 Priority generation\n• 🎁 Bonus promo codes',
        'choose_days': 'Choose duration:',
        'buy_premium': '📅 {days} days — {price} ⭐',
        'confirm_payment': '💎 Premium Payment\n\n📅 Duration: {days} days\n💰 Price: {price} ⭐\n\nClick the button below to activate:',
        'pay_stars': '⭐ Activate (demo)',
        'payment_success': '✅ Premium activated for {days} days!\n\n⏳ Valid until: {expiry}\n\n🔓 Unlimited search unlocked!',
        'promo_title': '🎟 Promo codes\n\nEnter promo code in chat.\n\nExample: /promo ABC12345\n\nPromo code can give:\n• Free premium\n• Bonus days',
        'promo_success': '✅ Promo code activated!\n\n🎁 Premium for {days} days received!\n⏳ Valid until: {expiry}\n\n🔓 Unlimited search unlocked!',
        'promo_invalid': '❌ Invalid promo code',
        'promo_used': '❌ Promo code already used maximum times',
        'referral_title': '👥 Referral System',
        'referral_link': '🔗 Your referral link:\nhttps://t.me/{bot}?start={ref_code}',
        'referral_stats': '📊 Invited: {count} people',
        'referral_reward': '🎁 For 10 invites — 1 day premium!\n🎁 If your referral buys premium — you get +5 days!',
        'referral_joined': '👤 User @{username} joined via your link!',
        'referral_reward_10': '🎉 You invited 10 people! Get 1 day of premium!',
        'referral_reward_purchase': '🎉 Your referral @{username} bought premium! You got +5 days!',
        'faved_yes': '✅ Yes',
        'faved_no': '❌ No',
        'digits_on_text': 'Enabled ✅',
        'digits_off_text': 'Disabled ❌',
        'favorites_full': '⚠️ Maximum 5 usernames in favorites! Remove some.',
        'payment_cancelled': '❌ Payment cancelled',
        'payment_error': '❌ Payment error. Please try again.',
        'no_referrals': '👥 You have no referrals yet.\n\nInvite friends and get bonuses!',
        'referral_code': '🔑 Your referral code: {code}',
        'set_lang': '🌐 Language set: {lang}',
        'premium_already': '✅ You already have premium!',
        'not_enough_stars': '❌ Not enough stars! Need: {price} ⭐',
        'friends': '👥 Friends',
        'info': 'ℹ️ Info',
        'referral_friends': '👥 Friends list:',
        'no_referral_friends': 'No friends yet'
    }
}

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def get_lang(user_id):
    if user_id not in user_settings:
        user_settings[user_id] = {'length': 5, 'digits': False, 'lang': 'ru'}
        save_data()
    return user_settings[user_id].get('lang', 'ru')

def get_text(user_id, key, **kwargs):
    lang = get_lang(user_id)
    text = TRANSLATIONS.get(lang, TRANSLATIONS['ru']).get(key, key)
    return text.format(**kwargs) if kwargs else text

def generate_ref_code(user_id):
    return f"{user_id}{random.randint(100, 999)}"

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
    return f"{days}d {hours}h {minutes}m"

def add_premium(user_id, days):
    expiry_date = datetime.now() + timedelta(days=days)
    user_premium[user_id] = {
        'expires': expiry_date.strftime('%Y-%m-%d %H:%M:%S'),
        'active': True
    }
    save_data()

def check_limit(user_id, length):
    if has_premium(user_id):
        return True, None, None
    
    if user_id not in user_searches:
        user_searches[user_id] = {'5': {'count': 0, 'reset_time': None}, '6': {'count': 0, 'reset_time': None}}
        save_data()
    
    str_length = str(length)
    if str_length not in user_searches[user_id]:
        user_searches[user_id][str_length] = {'count': 0, 'reset_time': None}
        save_data()
    
    data = user_searches[user_id][str_length]
    reset_time = data.get('reset_time')
    
    if reset_time:
        reset_dt = datetime.strptime(reset_time, '%Y-%m-%d %H:%M:%S')
        if datetime.now() >= reset_dt:
            data['count'] = 0
            data['reset_time'] = None
            save_data()
            return True, LIMITS.get(length, 10), None
    
    used = data.get('count', 0)
    limit = LIMITS.get(length, 10)
    
    if used >= limit:
        if reset_time:
            reset_dt = datetime.strptime(reset_time, '%Y-%m-%d %H:%M:%S')
            remaining = reset_dt - datetime.now()
            if remaining.total_seconds() < 0:
                data['count'] = 0
                data['reset_time'] = None
                save_data()
                return True, limit, None
            return False, limit, remaining
        else:
            reset_dt = datetime.now() + timedelta(hours=24)
            data['reset_time'] = reset_dt.strftime('%Y-%m-%d %H:%M:%S')
            save_data()
            remaining = reset_dt - datetime.now()
            return False, limit, remaining
    
    return True, limit, None

def increment_search(user_id, length):
    str_length = str(length)
    
    if user_id not in user_searches:
        user_searches[user_id] = {'5': {'count': 0, 'reset_time': None}, '6': {'count': 0, 'reset_time': None}}
    
    if str_length not in user_searches[user_id]:
        user_searches[user_id][str_length] = {'count': 0, 'reset_time': None}
    
    data = user_searches[user_id][str_length]
    
    if data.get('reset_time'):
        reset_dt = datetime.strptime(data['reset_time'], '%Y-%m-%d %H:%M:%S')
        if datetime.now() >= reset_dt:
            data['count'] = 0
            data['reset_time'] = None
    
    data['count'] += 1
    
    limit = LIMITS.get(length, 10)
    if data['count'] >= limit and not data.get('reset_time'):
        reset_dt = datetime.now() + timedelta(hours=24)
        data['reset_time'] = reset_dt.strftime('%Y-%m-%d %H:%M:%S')
    
    save_data()

def get_remaining_searches(user_id, length):
    if has_premium(user_id):
        return '♾ Unlimited', None
    
    str_length = str(length)
    
    if user_id not in user_searches:
        return LIMITS.get(length, 10), None
    
    if str_length not in user_searches[user_id]:
        return LIMITS.get(length, 10), None
    
    data = user_searches[user_id][str_length]
    reset_time = data.get('reset_time')
    
    if reset_time:
        reset_dt = datetime.strptime(reset_time, '%Y-%m-%d %H:%M:%S')
        if datetime.now() >= reset_dt:
            return LIMITS.get(length, 10), None
    
    used = data.get('count', 0)
    limit = LIMITS.get(length, 10)
    remaining = limit - used
    
    if remaining <= 0 and reset_time:
        reset_dt = datetime.strptime(reset_time, '%Y-%m-%d %H:%M:%S')
        remaining_time = reset_dt - datetime.now()
        if get_lang(user_id) == 'ru':
            return '⏳ 0 (через ' + format_time_ru(remaining_time) + ')', remaining_time
        else:
            return '⏳ 0 (in ' + format_time(remaining_time) + ')', remaining_time
    
    return remaining if remaining > 0 else 0, None

def format_time(td):
    if td is None:
        return ''
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours}h {minutes}m"

def format_time_ru(td):
    if td is None:
        return ''
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours}ч {minutes}м"

def generate_username(length, with_digits=False):
    chars = string.ascii_lowercase
    if with_digits:
        chars += string.digits
    first = random.choice(string.ascii_lowercase)
    rest = ''.join(random.choices(chars, k=length-1))
    return first + rest

async def is_username_free(username):
    try:
        await bot.get_entity(f'@{username}')
        return False
    except ValueError:
        return True
    except FloodWaitError as e:
        await asyncio.sleep(e.seconds)
        return None
    except Exception:
        return False

def check_fragment(username):
    try:
        url = f'https://fragment.com/username/{username}'
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return 'обнаружен ✅' 
        else:
            return 'не обнаружен ❌'
    except:
        return 'не удалось проверить ⚠️'

# ========== /START ==========
@bot.on(events.NewMessage(pattern='/start(?: (.*))?'))
async def start(event):
    user_id = event.sender_id
    args = event.pattern_match.group(1)
    
    # Обработка реферальной ссылки
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
                        await bot.send_message(referrer_id, get_text(referrer_id, 'referral_reward_10'))
                    except:
                        pass
                
                try:
                    username = event.sender.username or str(user_id)
                    await bot.send_message(referrer_id, get_text(referrer_id, 'referral_joined', username=username))
                except:
                    pass
    
    if user_id not in user_settings:
        user_settings[user_id] = {'length': 5, 'digits': False, 'lang': 'ru'}
        save_data()
    if user_id not in user_favorites:
        user_favorites[user_id] = []
        save_data()
    if user_id not in referrals:
        referrals[user_id] = {'invited': [], 'invited_by': None}
        save_data()
    
    premium_status = '✅ Активен' if has_premium(user_id) else '❌ Не активен'
    if get_lang(user_id) == 'en':
        premium_status = '✅ Active' if has_premium(user_id) else '❌ Not active'
    
    remaining_rem = get_premium_remaining(user_id) if has_premium(user_id) else None
    
    searches_5, _ = get_remaining_searches(user_id, 5)
    searches_6, _ = get_remaining_searches(user_id, 6)
    
    text = get_text(user_id, 'welcome') + '\n\n'
    text += get_text(user_id, 'premium_status', status=premium_status)
    if remaining_rem:
        text += '\n' + get_text(user_id, 'premium_remaining', time=remaining_rem)
    text += '\n\n' + get_text(user_id, 'limits', searches_5=str(searches_5), searches_6=str(searches_6))
    text += '\n\n' + get_text(user_id, 'choose_function')
    
    buttons = [
        [{'text': get_text(user_id, 'search'), 'callback': 'search'}],
        [{'text': get_text(user_id, 'favorites'), 'callback': 'favorites'}],
        [{'text': get_text(user_id, 'premium_shop'), 'callback': 'premium_shop'}],
        [{'text': get_text(user_id, 'promocode'), 'callback': 'promocode_menu'}],
        [{'text': get_text(user_id, 'settings'), 'callback': 'settings'}],
        [{'text': get_text(user_id, 'referral'), 'callback': 'referral'}]
    ]
    await event.respond(text, buttons=buttons)

# ========== ОБРАБОТЧИК КНОПОК ==========
@bot.on(events.CallbackQuery)
async def callback(event):
    user_id = event.sender_id
    data = event.data.decode()
    
    if data == 'main_menu':
        await start(event)
        return
    
    # ===== ПОИСК =====
    if data == 'search':
        settings = user_settings.get(user_id, {'length': 5, 'digits': False})
        length = settings['length']
        digits = settings['digits']
        
        can_search, limit, remaining_time = check_limit(user_id, length)
        
        if not can_search:
            reset_dt, remaining = None, None
            if user_id in user_searches and str(length) in user_searches[user_id]:
                reset_time = user_searches[user_id][str(length)].get('reset_time')
                if reset_time:
                    reset_dt = datetime.strptime(reset_time, '%Y-%m-%d %H:%M:%S')
                    remaining = reset_dt - datetime.now()
            
            if reset_dt:
                if get_lang(user_id) == 'ru':
                    time_str = format_time_ru(remaining)
                else:
                    time_str = format_time(remaining)
                text = get_text(user_id, 'limit_reached', 
                               limit=limit, 
                               length=length,
                               time=time_str,
                               reset_time=reset_dt.strftime('%d.%m.%Y %H:%M'))
            else:
                text = get_text(user_id, 'limit_reached',
                               limit=limit,
                               length=length,
                               time='24h',
                               reset_time='')
            
            buttons = [
                [{'text': get_text(user_id, 'premium_shop'), 'callback': 'premium_shop'}],
                [{'text': get_text(user_id, 'main_menu'), 'callback': 'main_menu'}]
            ]
            await event.edit(text, buttons=buttons)
            return
        
        await event.edit(get_text(user_id, 'searching'))
        
        found = None
        for _ in range(100):
            username = generate_username(length, digits)
            free = await is_username_free(username)
            if free is True:
                found = username
                break
            await asyncio.sleep(0.3)
        
        increment_search(user_id, length)
        
        if found:
            fragment_status = check_fragment(found)
            fav_list = user_favorites.get(user_id, [])
            is_faved = found in fav_list
            
            remaining, _ = get_remaining_searches(user_id, length)
            
            if get_lang(user_id) == 'ru':
                fragment_display = 'обнаружен ✅' if 'обнаружен' in fragment_status else 'не обнаружен ❌'
            else:
                fragment_display = 'detected ✅' if 'обнаружен' in fragment_status else 'not detected ❌'
            
            text = get_text(user_id, 'found',
                           username=found,
                           fragment=fragment_display,
                           faved=get_text(user_id, 'faved_yes') if is_faved else get_text(user_id, 'faved_no'),
                           count=len(fav_list))
            text += '\n\n' + get_text(user_id, 'remaining', remaining=str(remaining))
            
            buttons = []
            if is_faved:
                buttons.append([{'text': get_text(user_id, 'remove_fav'), 'callback': f'remove_fav_{found}'}])
            else:
                if len(fav_list) < 5:
                    buttons.append([{'text': get_text(user_id, 'add_fav'), 'callback': f'add_fav_{found}'}])
                else:
                    buttons.append([{'text': get_text(user_id, 'favorites_full'), 'callback': 'favorites_full'}])
            
            buttons.append([{'text': get_text(user_id, 'find_more'), 'callback': 'search'}])
            buttons.append([{'text': get_text(user_id, 'favorites'), 'callback': 'favorites'}])
            buttons.append([{'text': get_text(user_id, 'main_menu'), 'callback': 'main_menu'}])
            
            await event.edit(text, buttons=buttons)
        else:
            await event.edit(get_text(user_id, 'no_free'),
                           buttons=[[{'text': get_text(user_id, 'settings'), 'callback': 'settings'}]])
        return
    
    # ===== ДОБАВИТЬ В ИЗБРАННОЕ =====
    if data.startswith('add_fav_'):
        username = data.replace('add_fav_', '')
        fav_list = user_favorites.get(user_id, [])
        
        if username not in fav_list and len(fav_list) < 5:
            fav_list.append(username)
            user_favorites[user_id] = fav_list
            save_data()
            await event.answer(f'⭐ {username} добавлен!' if get_lang(user_id) == 'ru' else f'⭐ {username} added!', alert=True)
        
        await callback_search_result(event, username)
        return
    
    # ===== УБРАТЬ ИЗ ИЗБРАННОГО =====
    if data.startswith('remove_fav_'):
        username = data.replace('remove_fav_', '')
        fav_list = user_favorites.get(user_id, [])
        
        if username in fav_list:
            fav_list.remove(username)
            user_favorites[user_id] = fav_list
            save_data()
            await event.answer(f'🗑 {username} удалён!' if get_lang(user_id) == 'ru' else f'🗑 {username} removed!', alert=True)
        
        if 'from_list' in data:
            await show_favorites(event)
        else:
            await callback_search_result(event, username)
        return
    
    if data.startswith('remove_fav_from_list_'):
        username = data.replace('remove_fav_from_list_', '')
        fav_list = user_favorites.get(user_id, [])
        
        if username in fav_list:
            fav_list.remove(username)
            user_favorites[user_id] = fav_list
            save_data()
            await event.answer(f'🗑 {username} удалён!' if get_lang(user_id) == 'ru' else f'🗑 {username} removed!', alert=True)
        
        await show_favorites(event)
        return
    
    # ===== ИЗБРАННОЕ =====
    if data == 'favorites':
        await show_favorites(event)
        return
    
    # ===== ПРЕМИУМ МАГАЗИН =====
    if data == 'premium_shop':
        await show_premium_shop(event)
        return
    
    if data.startswith('buy_premium_'):
        days = int(data.replace('buy_premium_', ''))
        price = PREMIUM_PRICES.get(days)
        if not price:
            await event.answer('❌ Неверный срок!' if get_lang(user_id) == 'ru' else '❌ Invalid duration!', alert=True)
            return
        
        pending_payments[user_id] = {'days': days, 'price': price}
        
        text = get_text(user_id, 'confirm_payment', days=days, price=price)
        buttons = [
            [{'text': get_text(user_id, 'pay_stars'), 'callback': f'pay_stars_{days}'}],
            [{'text': get_text(user_id, 'back'), 'callback': 'premium_shop'}]
        ]
        await event.edit(text, buttons=buttons)
        return
    
    if data.startswith('pay_stars_'):
        days = int(data.replace('pay_stars_', ''))
        price = PREMIUM_PRICES.get(days)
        
        # Проверка на уже активный премиум
        if has_premium(user_id):
            await event.answer(get_text(user_id, 'premium_already'), alert=True)
            return
        
        # Активация премиума
        add_premium(user_id, days)
        
        # Проверка: есть ли у пользователя реферер?
        if user_id in referrals and referrals[user_id].get('invited_by'):
            referrer_id = referrals[user_id]['invited_by']
            add_premium(referrer_id, 5)
            try:
                username = event.sender.username or str(user_id)
                await bot.send_message(referrer_id, get_text(referrer_id, 'referral_reward_purchase', username=username))
            except:
                pass
        
        expiry_date = datetime.now() + timedelta(days=days)
        await event.edit(get_text(user_id, 'payment_success', days=days, expiry=expiry_date.strftime('%d.%m.%Y %H:%M')),
                        buttons=[[{'text': get_text(user_id, 'search'), 'callback': 'search'}],
                                [{'text': get_text(user_id, 'main_menu'), 'callback': 'main_menu'}]])
        return
    
    # ===== ПРОМОКОДЫ =====
    if data == 'promocode_menu':
        await event.edit(get_text(user_id, 'promo_title'),
                        buttons=[[{'text': get_text(user_id, 'back'), 'callback': 'main_menu'}]])
        return
    
    # ===== РЕФЕРАЛЫ =====
    if data == 'referral':
        await show_referral(event)
        return
    
    if data == 'referral_friends':
        await show_referral_friends(event)
        return
    
    # ===== НАСТРОЙКИ =====
    if data == 'settings':
        settings = user_settings.get(user_id, {'length': 5, 'digits': False, 'lang': 'ru'})
        length = settings['length']
        digits = settings['digits']
        lang = settings.get('lang', 'ru')
        
        text = get_text(user_id, 'settings_title') + '\n\n'
        text += get_text(user_id, 'settings_length', length=length) + '\n'
        text += get_text(user_id, 'settings_digits', digits=get_text(user_id, 'digits_on_text') if digits else get_text(user_id, 'digits_off_text')) + '\n'
        text += get_text(user_id, 'settings_lang', lang='🇷🇺 Русский' if lang == 'ru' else '🇬🇧 English')
        
        buttons = [
            [{'text': get_text(user_id, 'length_5') if length == 6 else get_text(user_id, 'length_6'), 'callback': 'toggle_length'}],
            [{'text': get_text(user_id, 'digits_off') if digits else get_text(user_id, 'digits_on'), 'callback': 'toggle_digits'}],
            [{'text': get_text(user_id, 'lang_ru') if lang == 'en' else get_text(user_id, 'lang_en'), 'callback': 'toggle_lang'}],
            [{'text': get_text(user_id, 'main_menu'), 'callback': 'main_menu'}]
        ]
        await event.edit(text, buttons=buttons)
        return
    
    if data == 'toggle_length':
        current = user_settings[user_id].get('length', 5)
        user_settings[user_id]['length'] = 6 if current == 5 else 5
        save_data()
        await event.edit('✅ ' + ('Set: 6 letters' if get_lang(user_id) == 'en' else 'Установлено: 6 букв') if user_settings[user_id]['length'] == 6 else ('Set: 5 letters' if get_lang(user_id) == 'en' else 'Установлено: 5 букв'),
                        buttons=[[{'text': get_text(user_id, 'back'), 'callback': 'settings'}]])
        return
    
    if data == 'toggle_digits':
        user_settings[user_id]['digits'] = not user_settings[user_id].get('digits', False)
        save_data()
        await event.edit('✅ ' + ('Digits enabled' if get_lang(user_id) == 'en' else 'Цифры включены') if user_settings[user_id]['digits'] else ('Digits disabled' if get_lang(user_id) == 'en' else 'Цифры выключены'),
                        buttons=[[{'text': get_text(user_id, 'back'), 'callback': 'settings'}]])
        return
    
    if data == 'toggle_lang':
        current_lang = user_settings[user_id].get('lang', 'ru')
        new_lang = 'en' if current_lang == 'ru' else 'ru'
        user_settings[user_id]['lang'] = new_lang
        save_data()
        await event.edit(get_text(user_id, 'set_lang', lang='🇷🇺 Русский' if new_lang == 'ru' else '🇬🇧 English'),
                        buttons=[[{'text': get_text(user_id, 'back'), 'callback': 'settings'}]])
        return
    
    if data == 'favorites_full':
        await event.answer(get_text(user_id, 'favorites_full'), alert=True)
        return

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
async def callback_search_result(event, username):
    user_id = event.sender_id
    fragment_status = check_fragment(username)
    fav_list = user_favorites.get(user_id, [])
    is_faved = username in fav_list
    
    if get_lang(user_id) == 'ru':
        fragment_display = 'обнаружен ✅' if 'обнаружен' in fragment_status else 'не обнаружен ❌'
    else:
        fragment_display = 'detected ✅' if 'обнаружен' in fragment_status else 'not detected ❌'
    
    text = get_text(user_id, 'found',
                   username=username,
                   fragment=fragment_display,
                   faved=get_text(user_id, 'faved_yes') if is_faved else get_text(user_id, 'faved_no'),
                   count=len(fav_list))
    
    buttons = []
    if is_faved:
        buttons.append([{'text': get_text(user_id, 'remove_fav'), 'callback': f'remove_fav_{username}'}])
    else:
        if len(fav_list) < 5:
            buttons.append([{'text': get_text(user_id, 'add_fav'), 'callback': f'add_fav_{username}'}])
        else:
            buttons.append([{'text': get_text(user_id, 'favorites_full'), 'callback': 'favorites_full'}])
    
    buttons.append([{'text': get_text(user_id, 'find_more'), 'callback': 'search'}])
    buttons.append([{'text': get_text(user_id, 'favorites'), 'callback': 'favorites'}])
    buttons.append([{'text': get_text(user_id, 'main_menu'), 'callback': 'main_menu'}])
    
    await event.edit(text, buttons=buttons)

async def show_favorites(event):
    user_id = event.sender_id
    fav_list = user_favorites.get(user_id, [])
    
    if not fav_list:
        text = get_text(user_id, 'no_favorites')
        buttons = [
            [{'text': get_text(user_id, 'search'), 'callback': 'search'}],
            [{'text': get_text(user_id, 'main_menu'), 'callback': 'main_menu'}]
        ]
        await event.edit(text, buttons=buttons)
        return
    
    text = get_text(user_id, 'favorites_title') + '\n\n'
    for i, username in enumerate(fav_list, 1):
        free = await is_username_free(username)
        if get_lang(user_id) == 'ru':
            status = '🟢 Свободен' if free else '🔴 Занят'
        else:
            status = '🟢 Free' if free else '🔴 Taken'
        fragment = check_fragment(username)
        if get_lang(user_id) == 'ru':
            fragment_display = 'обнаружен ✅' if 'обнаружен' in fragment else 'не обнаружен ❌'
        else:
            fragment_display = 'detected ✅' if 'обнаружен' in fragment else 'not detected ❌'
        text += f"{i}. @{username} — {status} | Fragment: {fragment_display}\n"
    
    buttons = []
    for username in fav_list:
        buttons.append([{'text': f'🗑 Delete @{username}', 'callback': f'remove_fav_from_list_{username}'}])
    
    buttons.append([{'text': get_text(user_id, 'search'), 'callback': 'search'}])
    buttons.append([{'text': get_text(user_id, 'main_menu'), 'callback': 'main_menu'}])
    
    await event.edit(text, buttons=buttons)

async def show_premium_shop(event):
    user_id = event.sender_id
    has_prem = has_premium(user_id)
    remaining = get_premium_remaining(user_id) if has_prem else None
    
    text = get_text(user_id, 'premium_title') + '\n\n'
    text += get_text(user_id, 'premium_active') if has_prem else get_text(user_id, 'premium_inactive')
    if remaining:
        text += '\n⏳ ' + get_text(user_id, 'premium_remaining', time=remaining)
    text += '\n\n' + get_text(user_id, 'premium_features') + '\n\n'
    text += get_text(user_id, 'choose_days')
    
    buttons = []
    for days in sorted(PREMIUM_PRICES.keys()):
        price = PREMIUM_PRICES[days]
        buttons.append([{'text': get_text(user_id, 'buy_premium', days=days, price=price), 'callback': f'buy_premium_{days}'}])
    
    buttons.append([{'text': get_text(user_id, 'main_menu'), 'callback': 'main_menu'}])
    
    await event.edit(text, buttons=buttons)

async def show_referral(event):
    user_id = event.sender_id
    ref_data = referrals.get(user_id, {'invited': [], 'invited_by': None})
    invited_count = len(ref_data.get('invited', []))
    
    ref_code = generate_ref_code(user_id)
    
    text = get_text(user_id, 'referral_title') + '\n\n'
    text += get_text(user_id, 'referral_link', bot=BOT_USERNAME, ref_code=ref_code) + '\n\n'
    text += get_text(user_id, 'referral_code', code=ref_code) + '\n\n'
    text += get_text(user_id, 'referral_stats', count=invited_count) + '\n\n'
    text += get_text(user_id, 'referral_reward')
    
    buttons = [
        [{'text': get_text(user_id, 'friends'), 'callback': 'referral_friends'}],
        [{'text': get_text(user_id, 'main_menu'), 'callback': 'main_menu'}]
    ]
    await event.edit(text, buttons=buttons)

async def show_referral_friends(event):
    user_id = event.sender_id
    ref_data = referrals.get(user_id, {'invited': [], 'invited_by': None})
    invited = ref_data.get('invited', [])
    
    text = get_text(user_id, 'referral_friends') + '\n\n'
    
    if not invited:
        text += get_text(user_id, 'no_referral_friends')
    else:
        for i, friend_id in enumerate(invited, 1):
            try:
                user = await bot.get_entity(friend_id)
                name = user.username or user.first_name or str(friend_id)
                text += f"{i}. @{name}\n"
            except:
                text += f"{i}. {friend_id}\n"
    
    buttons = [[{'text': get_text(user_id, 'back'), 'callback': 'referral'}]]
    await event.edit(text, buttons=buttons)

# ========== ОБРАБОТКА ПРОМОКОДОВ ==========
@bot.on(events.NewMessage(pattern='/promo .+'))
async def handle_promo(event):
    user_id = event.sender_id
    code = event.raw_text.replace('/promo', '').strip().upper()
    
    if code not in promocodes:
        await event.reply(get_text(user_id, 'promo_invalid'))
        return
    
    promo = promocodes[code]
    if promo['used'] >= promo['activations']:
        await event.reply(get_text(user_id, 'promo_used'))
        return
    
    promo['used'] += 1
    reward = promo['reward']
    
    days_map = {'premium_1': 1, 'premium_10': 10, 'premium_15': 15, 'premium_30': 30}
    days = days_map.get(reward, 1)
    
    add_premium(user_id, days)
    expiry_date = datetime.now() + timedelta(days=days)
    save_data()
    
    await event.reply(get_text(user_id, 'promo_success', days=days, expiry=expiry_date.strftime('%d.%m.%Y %H:%M')))

# ========== АДМИН-КОМАНДА ДЛЯ СОЗДАНИЯ ПРОМОКОДА ==========
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
        
        await event.reply(f"""✅ Промокод создан!

🎟 Код: `{code}`
📊 Активаций: {activations}
🎁 Награда: {reward}

Используйте: /promo {code}""")
    except:
        await event.reply('❌ Формат: /create_promo [кол-во_активаций] [награда]\nНаграды: premium_1, premium_10, premium_15, premium_30')

# ========== ЗАПУСК ==========
print('🤖 Бот запущен!')
print('Лимиты: 5 букв — 10/день, 6 букв — 50/день')
print('Для создания промокода: /create_promo 5 premium_30')
bot.run_until_disconnected()