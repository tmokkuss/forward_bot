from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import InputMedia, InputMediaPhoto, InputMediaVideo, Document
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

bot = Bot(token='API-token', parse_mode='HTML')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
TELEGRAM_SUPPORT_CHAT_ID = "TELEGRAM_SUPPORT_CHAT_ID"
PHOTOS_ID = []
photo_delivered: set[int] = set()


@dp.message_handler(commands=['start'])
async def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
    join = types.KeyboardButton('/help')
    markup.add(join)
    mess = f'Привет, {message.from_user.first_name} 👋 \nЭтот бот создан специально для вопросов \nНажимай на кнопку снизу или же напиши мне "/help" '
    await bot.send_message(message.chat.id, mess, reply_markup=markup)


class Form(StatesGroup):
    email = State()
    ask = State()


@dp.message_handler(commands=['help'], state=None)
async def start(message: types.Message):
    await Form.email.set()
    await bot.send_message(message.chat.id,
                           f'{message.from_user.first_name}, для начала пришли мне cвой электронный адрес 📥')


@dp.message_handler(state=Form.email)
async def get_email(message: types.Message, state: FSMContext):
    answer = message.text
    async with state.proxy() as data:
        data["email"] = answer
    await Form.ask.set()
    await bot.send_message(message.chat.id,
                           f'{message.from_user.first_name}, пришли мне свой вопрос!'
                           f'\n\n<b>Как пользоваться</b>:\n'
                           f'1. Отправь одним сообщением фото/видео и вопрос.\n'
                           f'2. Если у тебя фото, то поставь галочку на "Сжать изображение" 🥰')


@dp.message_handler(state=Form.ask)
async def process_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    email = data.get("email")
    mess = f'Спасибо за вопрос! Я постараюсь ответить тебе в течение дня!\nА пока ждешь, можешь посмотреть вдохновения и не только в моем канале ❤'
    markup = types.InlineKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
    channel_btn = types.InlineKeyboardButton('Вдохновение', url='https://t.me/webdesign_uiux')
    markup.add(channel_btn)
    await state.finish()
    await bot.send_message(TELEGRAM_SUPPORT_CHAT_ID, f'E-mail: {email}\n'
                                                     f'first name: {message.from_user.first_name}\n'
                                                     f'last name: {message.from_user.last_name}\n'
                                                     f'username: @{message.from_user.username}\n'
                                                     f'USER_CHAT_ID: {message.chat.id}\n'
                                                     f'<b>Вопрос: {message.text}</b>\n')
    await bot.send_message(message.chat.id, mess, reply_markup=markup)


async def say_thanks(user: types.User):
    mess = f'Спасибо за вопрос! Я постараюсь ответить тебе в течение дня!\nА пока ждешь, можешь посмотреть вдохновения и не только в моем канале ❤'
    if user.id in photo_delivered:
        return
    photo_delivered.add(user.id)
    markup = types.InlineKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
    channel_btn = types.InlineKeyboardButton('Вдохновение', url='https://t.me/webdesign_uiux')
    markup.add(channel_btn)
    await bot.send_message(user.id, mess, reply_markup=markup)


@dp.message_handler(state=Form.ask, content_types=['photo'])
async def forward_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    email = data.get("email")
    await say_thanks(message.from_user)
    photo = message.photo[-1].file_id
    media = [InputMediaPhoto(photo, caption=f'E-mail: {email}\n'
                                            f'first name: {message.from_user.first_name}\n'
                                            f'last name: {message.from_user.last_name}\n'
                                            f'username: @{message.from_user.username}\n'
                                            f'USER_CHAT_ID: {message.chat.id}\n'
                                            f'<b>Вопрос: {message.caption}</b>')]
    await bot.send_media_group(TELEGRAM_SUPPORT_CHAT_ID, media=media)  # media=media
    await state.finish()


@dp.message_handler(state=Form.ask, content_types=['video'])
async def forward_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    email = data.get("email")
    await say_thanks(message.from_user)
    video = message.video.file_id
    await bot.send_video(TELEGRAM_SUPPORT_CHAT_ID, video=video, caption=f'E-mail: {email}\n'
                                                                        f'first name: {message.from_user.first_name}\n'
                                                                        f'last name: {message.from_user.last_name}\n'
                                                                        f'username: @{message.from_user.username}\n'
                                                                        f'USER_CHAT_ID: {message.chat.id}\n'
                                                                        f'<b>Вопрос: {message.caption}</b>')
    await state.finish()


@dp.message_handler()
async def answer_the_ask(message: types.Message, state: FSMContext):
    if message.chat.id == TELEGRAM_SUPPORT_CHAT_ID:
        if message.reply_to_message:
            try:
                await message.reply_to_message.reply("Вопрос закрыт!")
                answer = message.text
                user_info = message.reply_to_message.text
                USER = user_info.split('\n')
                for line in USER:
                    if line.startswith('USER_CHAT_ID: '):
                        USER_CHAT_ID = line.lstrip('USER_CHAT_ID: ')
                        await bot.send_message(USER_CHAT_ID, answer)
            except:
                answer = message.text
                user_info = message.reply_to_message.caption
                USER = user_info.split('\n')
                for line in USER:
                    if line.startswith('USER_CHAT_ID: '):
                        USER_CHAT_ID = line.lstrip('USER_CHAT_ID: ')
                        await bot.send_message(USER_CHAT_ID, answer)
    elif message.text == "Спасибо" or message.text == "Thanks" or message.text.startswith(
            "Cпаc") or message.text == 'Дякуємо':
        mess = f'{message.from_user.first_name}, всегда пожалуйста!'
        await bot.send_message(message.chat.id, mess)
    else:
        mess = 'Пожалуйста, следуй инструкции'
        await bot.send_message(message.chat.id, mess)


@dp.message_handler(content_types=['photo'])
async def answer_the_photo(message: types.Message, state: FSMContext):
    if message.chat.id == TELEGRAM_SUPPORT_CHAT_ID:
        if message.reply_to_message:
            try:
                await message.reply_to_message.reply("Фото отправлено!")
                answer = message.photo[-1].file_id
                answer_text = message.caption
                user_info = message.reply_to_message.caption
                USER = user_info.split('\n')
                for line in USER:
                    if line.startswith('USER_CHAT_ID: '):
                        USER_CHAT_ID = line.lstrip('USER_CHAT_ID: ')
                        await bot.send_photo(USER_CHAT_ID, answer)
                        await bot.send_message(USER_CHAT_ID, answer_text)
            except:
                await message.reply_to_message.reply("Фото отправлено!")
                answer = message.photo[-1].file_id
                answer_text = message.caption
                user_info = message.reply_to_message.text
                USER = user_info.split('\n')
                for line in USER:
                    if line.startswith('USER_CHAT_ID: '):
                        USER_CHAT_ID = line.lstrip('USER_CHAT_ID: ')
                        await bot.send_photo(USER_CHAT_ID, answer)
                        await bot.send_message(USER_CHAT_ID, answer_text)


@dp.message_handler(content_types=['video'])
async def answer_the_photo(message: types.Message, state: FSMContext):
    if message.chat.id == TELEGRAM_SUPPORT_CHAT_ID:
        if message.reply_to_message:
            await message.reply_to_message.reply("Видео отправлено!")
            answer = message.video.file_id
            answer_text = message.caption
            user_info = message.reply_to_message.caption
            USER = user_info.split('\n')
            for line in USER:
                if line.startswith('USER_CHAT_ID: '):
                    USER_CHAT_ID = line.lstrip('USER_CHAT_ID: ')
                    await bot.send_video(USER_CHAT_ID, answer)
                    await bot.send_message(USER_CHAT_ID, answer_text)


executor.start_polling(dp, skip_updates=True)
