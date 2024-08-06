import os
import asyncio
from PIL import Image
from aiogram import Bot, Dispatcher, executor
from aiogram.types import Message, ContentType, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.exceptions import MessageNotModified

# Replace with your FRAME_PATHs and TOKEN
from config import TOKEN, FRAME_PATH_0, FRAME_PATH_1

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Keyboard for initial choices
keyboard_initial = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard_initial.add(KeyboardButton('Old'), KeyboardButton('New'))

# Keyboard for size adjustment
keyboard_size_adjust = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard_size_adjust.add(KeyboardButton('+'), KeyboardButton('-'))

# Dictionary to store user choices
user_choice = {}

# Dictionary to store downloaded photo, processed image paths, and current sizes
downloaded_photos = {}
processed_images = {}
current_sizes = {}


# Function to handle initial message
@dp.message_handler(commands=['start'])
async def handle_start(message: Message):
    await message.answer("Привет! Выберите тип обработки фотографии:", reply_markup=keyboard_initial)

# Function to handle 'Old' choice
@dp.message_handler(lambda message: message.text.lower() == 'old')
async def handle_old_choice(message: Message):
    user_choice[message.chat.id] = 'old'
    await message.answer("Выбрана старая обработка. Пожалуйста, загрузите фотографию.")

# Function to handle 'New' choice
@dp.message_handler(lambda message: message.text.lower() == 'new')
async def handle_new_choice(message: Message):
    user_choice[message.chat.id] = 'new'
    await message.answer("Выбрана новая обработка. Пожалуйста, загрузите фотографию.")

# Function to handle photo upload
@dp.message_handler(content_types=[ContentType.PHOTO])
async def handle_photo(message: Message):
    chat_id = message.chat.id
    if chat_id in user_choice:
        choice = user_choice[chat_id]
        photo = message.photo[-1]
        photo_id = photo.file_id

        photo_obj = await bot.get_file(photo_id)
        photo_path = photo_obj.file_path

        downloaded_photo = await bot.download_file(photo_path)
        downloaded_photos[chat_id] = downloaded_photo  # Store downloaded photo

        if choice == 'old':
            await handle_old_photo(message, downloaded_photo)
        elif choice == 'new':
            await handle_new_photo(message, downloaded_photo)
        else:
            await message.answer("Пожалуйста, выберите тип обработки сначала.")
    else:
        await message.answer("Пожалуйста, выберите тип обработки сначала.")

# Function to process photo with 'Old' method
async def handle_old_photo(message: Message, downloaded_photo):
    try:
        user_photo = Image.open(downloaded_photo)
        frame = Image.open(FRAME_PATH_0)

        frame_width, frame_height = frame.size
        user_width, user_height = user_photo.size

        x_offset = (frame_width - user_width) // 2
        y_offset = (frame_height - user_height) // 2

        frame.paste(user_photo, (x_offset, y_offset))

        output_path = f'result_{message.chat.id}.jpg'
        frame.save(output_path)

        if os.path.exists(output_path):
            await message.answer_photo(open(output_path, 'rb'), reply_markup=keyboard_size_adjust)
            processed_images[message.chat.id] = output_path  # Store processed image path
            current_sizes[message.chat.id] = (user_width, user_height)  # Store current size

            # Schedule automatic deletion after 1 minute
            await schedule_image_cleanup(output_path, message.chat.id)
        else:
            await message.answer("Ошибка при обработке изображения. Пожалуйста, попробуйте еще раз.")

    except Exception as e:
        print(f"Error processing image: {e}")
        await message.answer("Произошла ошибка при обработке изображения.")

# Function to process photo with 'New' method
async def handle_new_photo(message: Message, downloaded_photo):
    try:
        user_photo = Image.open(downloaded_photo)
        frame = Image.open(FRAME_PATH_1)

        user_width, user_height = user_photo.size
        new_width = user_width
        new_height = user_height

        user_photo_resized = user_photo.resize((new_width, new_height))

        frame_width, frame_height = frame.size

        x_offset = (frame_width - new_width) // 2
        y_offset = 75  

        frame.paste(user_photo_resized, (x_offset, y_offset))

        output_path = f'result_{message.chat.id}.jpg'
        frame.save(output_path)

        if os.path.exists(output_path):
            await message.answer_photo(open(output_path, 'rb'), reply_markup=keyboard_size_adjust)
            processed_images[message.chat.id] = output_path  # Store processed image path
            current_sizes[message.chat.id] = (new_width, new_height)  # Store current size

            # Schedule automatic deletion after 1 minute
            await schedule_image_cleanup(output_path, message.chat.id)
        else:
            await message.answer("Ошибка при обработке изображения. Пожалуйста, попробуйте еще раз.")

    except Exception as e:
        print(f"Error processing image: {e}")
        await message.answer("Произошла ошибка при обработке изображения.")

# Function to handle size increase button
@dp.message_handler(lambda message: message.text == '+')
async def handle_size_increase(message: Message):
    await handle_image_resize(message, factor=1.05)  # Increase by 5%

# Function to handle size decrease button
@dp.message_handler(lambda message: message.text == '-')
async def handle_size_decrease(message: Message):
    await handle_image_resize(message, factor=0.95)  # Decrease by 5%



# Function to resize image and send again
async def handle_image_resize(message: Message, factor: float):
    chat_id = message.chat.id
    if chat_id in downloaded_photos:
        downloaded_photo = downloaded_photos[chat_id]
        try:
            user_photo = Image.open(downloaded_photo)
            frame = Image.open(FRAME_PATH_1)

            # Get original size if current size is not set
            if chat_id not in current_sizes:
                user_width, user_height = user_photo.size
                current_sizes[chat_id] = (user_width, user_height)

            # Get current size
            current_width, current_height = current_sizes[chat_id]

            # Calculate new size based on current size and factor
            new_width = int(current_width * factor)
            new_height = int(current_height * factor)

            user_photo_resized = user_photo.resize((new_width, new_height))

            frame_width, frame_height = frame.size

            x_offset = (frame_width - new_width) // 2
            y_offset = 75

            result_frame = frame.copy()
            result_frame.paste(user_photo_resized, (x_offset, y_offset))

            output_path = f'result_{message.chat.id}.jpg'
            result_frame.save(output_path)

            if os.path.exists(output_path):
                try:
                    await message.answer_photo(open(output_path, 'rb'), reply_markup=keyboard_size_adjust)
                    processed_images[message.chat.id] = output_path  # Update processed image path
                    current_sizes[message.chat.id] = (new_width, new_height)  # Update current size
                except MessageNotModified:
                    pass
            else:
                await message.answer("Ошибка при обработке изображения. Пожалуйста, попробуйте еще раз.")

        except Exception as e:
            print(f"Error processing resized image: {e}")
            await message.answer("Произошла ошибка при обработке измененного изображения.")


async def schedule_image_cleanup(image_path: str, chat_id: int):
    try:
        # Schedule cleanup after 1 minute
        await asyncio.sleep(120)
        if os.path.exists(image_path):
            os.remove(image_path)
            downloaded_photos.pop(chat_id, None)
            processed_images.pop(chat_id, None)
            current_sizes.pop(chat_id, None)
            print(f"Deleted temporary image: {image_path}")
    except Exception as e:
        print(f"Error cleaning up image: {e}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
