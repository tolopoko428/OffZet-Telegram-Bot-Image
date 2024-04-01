import asyncio
import os
from PIL import Image
from aiogram import Dispatcher, Bot
from aiogram.types import Message, ContentType
from config import TOKEN, FRAME_PATH

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

sent_photos = {}  # Словарь для отслеживания уже отправленных фотографий по каждому чату
@dp.message_handler(content_types=['photo'])
async def handle_photos(message: Message):
    # Получаем информацию о фотографии
    photo = message.photo[-1]
    photo_id = photo.file_id

    # Получаем объект файла фотографии
    photo_obj = await bot.get_file(photo_id)
    photo_path = photo_obj.file_path

    # Скачиваем фотографию
    downloaded_photo = await bot.download_file(photo_path)

    # Открываем фотографию с рамкой
    frame = Image.open(FRAME_PATH)

    # Открываем скачанную фотографию
    user_photo = Image.open(downloaded_photo)

    # Получаем размеры рамки
    frame_width, frame_height = frame.size

    # Уменьшаем размер пользовательской фотографии на 35%
    new_width = int(user_photo.width * 0.83)
    new_height = int(user_photo.height * 0.83)
    user_photo_resized = user_photo.resize((new_width, new_height))

    # Вычисляем координаты для центрирования фотографии на рамке
    x_offset = (frame_width - new_width) // 2
    y_offset = (frame_height - new_height) // 2

    # Накладываем уменьшенную фотографию на рамку
    frame.paste(user_photo_resized, (x_offset, y_offset))

    # Сохраняем результат
    output_path = f'result_{message.chat.id}.jpg'  # Имя файла с результатом
    frame.save(output_path)

    # Проверяем, существует ли файл
    if os.path.exists(output_path):
        # Отправляем результат пользователю
        await message.answer_photo(open(output_path, 'rb'))
    else:
        await message.answer("Ошибка при обработке изображения. Пожалуйста, попробуйте еще раз.")

    downloaded_photo.close()

async def main():
    await dp.start_polling()

if __name__ == '__main__':
    asyncio.run(main())
