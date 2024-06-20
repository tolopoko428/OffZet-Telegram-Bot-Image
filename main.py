import os
from PIL import Image
from aiogram import Bot, Dispatcher, executor
from aiogram.types import Message, ContentType, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import exceptions
from config import TOKEN, FRAME_PATH_0, FRAME_PATH_1

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Создаем клавиатуру с кнопками "Old" и "New"
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton('Old'), KeyboardButton('New'))

# Словарь для хранения выбора пользователя (тип обработки: 'old' или 'new')
user_choice = {}

# Функция для обработки сообщений с текстом 'ping'
@dp.message_handler(lambda message: message.text.lower() == 'ping')
async def handle_ping(message: Message):
    await message.answer('pong')

# Обработчик для начального сообщения
@dp.message_handler(commands=['start'])
async def handle_start(message: Message):
    await message.answer("Привет! Выберите тип обработки фотографии:", reply_markup=keyboard)

# Обработчик для кнопки "Old"
@dp.message_handler(lambda message: message.text.lower() == 'old')
async def handle_old_choice(message: Message):
    user_choice[message.chat.id] = 'old'  # Сохраняем выбор пользователя
    await message.answer("Выбрана старая обработка. Пожалуйста, загрузите фотографию.")

# Обработчик для кнопки "New"
@dp.message_handler(lambda message: message.text.lower() == 'new')
async def handle_new_choice(message: Message):
    user_choice[message.chat.id] = 'new'  # Сохраняем выбор пользователя
    await message.answer("Выбрана новая обработка. Пожалуйста, загрузите фотографию.")

# Обработчик для получения фотографии
@dp.message_handler(content_types=[ContentType.PHOTO])
async def handle_photo(message: Message):
    chat_id = message.chat.id
    if chat_id in user_choice:
        choice = user_choice[chat_id]
        if choice == 'old':
            await handle_old_photo(message)
        elif choice == 'new':
            await handle_new_photo(message)
        else:
            await message.answer("Пожалуйста, выберите тип обработки сначала.")
    else:
        await message.answer("Пожалуйста, выберите тип обработки сначала.")

# Функция для старой обработки фотографии
async def handle_old_photo(message: Message):
    try:
        # Получаем информацию о фотографии
        photo = message.photo[-1]
        photo_id = photo.file_id

        # Получаем объект файла фотографии
        photo_obj = await bot.get_file(photo_id)
        photo_path = photo_obj.file_path

        # Скачиваем фотографию
        downloaded_photo = await bot.download_file(photo_path)

        # Открываем фотографию с рамкой
        frame = Image.open(FRAME_PATH_0)

        # Открываем скачанную фотографию
        user_photo = Image.open(downloaded_photo)

        # Получаем размеры рамки и фотографии пользователя
        frame_width, frame_height = frame.size
        user_width, user_height = user_photo.size

        # Вычисляем координаты для центрирования фотографии пользователя на рамке
        x_offset = (frame_width - user_width) // 2
        y_offset = (frame_height - user_height) // 4  # Смещаем фото немного вниз от центра

        # Накладываем фотографию пользователя на рамку
        frame.paste(user_photo, (x_offset, y_offset))

        # Сохраняем результат
        output_path = f'result_{message.chat.id}.jpg'  # Имя файла с результатом
        frame.save(output_path)

        # Проверяем, существует ли файл
        if os.path.exists(output_path):
            # Отправляем результат пользователю
            await message.answer_photo(open(output_path, 'rb'))
        else:
            await message.answer("Ошибка при обработке изображения. Пожалуйста, попробуйте еще раз.")

        # Удаляем временный файл
        os.remove(output_path)

        downloaded_photo.close()

    except exceptions.MessagePhotoInvalidDimensions:
        await message.answer("Извините, но ваше изображение слишком маленькое.")

async def handle_new_photo(message: Message):
    try:
        # Получаем информацию о фотографии
        photo = message.photo[-1]
        photo_id = photo.file_id

        # Получаем объект файла фотографии
        photo_obj = await bot.get_file(photo_id)
        photo_path = photo_obj.file_path

        # Скачиваем фотографию
        downloaded_photo = await bot.download_file(photo_path)

        # Открываем фотографию с рамкой
        frame = Image.open(FRAME_PATH_1)
        user_photo = Image.open(downloaded_photo)

        # Получаем размеры фотографии пользователя
        user_width, user_height = user_photo.size

        # Увеличиваем размер фотографии пользователя на 50%
        new_width = int(user_width * 1.3)
        new_height = int(user_height * 1.3)
        user_photo = user_photo.resize((new_width, new_height))

        # Получаем размеры рамки
        frame_width, frame_height = frame.size

        # Вычисляем координаты для центрирования фотографии пользователя на рамке
        x_offset = (frame_width - new_width) // 2
        y_offset = 130  # Расстояние от верхнего края рамки до фотографии пользователя

        # Накладываем фотографию пользователя на рамку сверху
        frame.paste(user_photo, (x_offset, y_offset))

        # Сохраняем результат
        output_path = f'result_{message.chat.id}.jpg'  # Имя файла с результатом
        frame.save(output_path)

        # Проверяем, существует ли файл
        if os.path.exists(output_path):
            # Отправляем результат пользователю
            await message.answer_photo(open(output_path, 'rb'))
        else:
            await message.answer("Ошибка при обработке изображения. Пожалуйста, попробуйте еще раз.")

        # Удаляем временный файл
        os.remove(output_path)

        downloaded_photo.close()

    except exceptions.MessagePhotoInvalidDimensions:
        await message.answer("Извините, но ваше изображение слишком маленькое.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
