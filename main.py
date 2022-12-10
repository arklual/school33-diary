from api.settings import TELEGRAM_TOKEN, LAST_NAMES
from api.school33api import School33Api
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.utils.markdown import hbold, hunderline
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import aioschedule
import asyncio
import copy

bot = Bot(token=TELEGRAM_TOKEN, parse_mode='HTML')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
api = School33Api()
@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.answer(f'Привет, {message.from_user.first_name}. Ты уже прочитал описание и знаешь, чем я могу тебе помочь.\n' 
    + 'Если вдруг ты не прочитал описание, то я твой электронный дневник, но только в телеграмме и более крутой. \n\n ' +
    "📍 " + hbold(' Что я могу?') + '\n'
    + '🚩 Пока только присылать твои оценки в данном триместре по запросу (но актуальные, в отличие от официального дневника)' + '\n' +
    '🚩 Но скоро я смогу присылать тебе новые оценки в тот момент, когда ты их получаешь и ' + hunderline('много чего ещё') + ' (пока сохраним это в интриге). ' + 
    'С помощью меня ты сможешь понять, что у тебя получается лучше,  а что хуже.\n\n'
    '🆘\nСправка: /help', parse_mode='HTML'
    )

@dp.message_handler(commands=['help'])
async def help_user(message: types.Message):
    await message.answer("""Вот команды, которые доступны нашему боту.
    /get_marks - узнать о твоих текущих оценках в этом триместре""")

@dp.message_handler(commands=['get_marks'])
async def send_marks(message: types.Message):
    last_name = LAST_NAMES[str(message.from_id)]
    for st in api.students:
        if st.name.split(' ')[1] == last_name:
            await message.answer('Твои оценки:')
            for subject in st.subjects:
                if subject.marks != []:
                    await message.answer(f'{subject.name} {subject.average_mark} {subject.marks}')

async def send_if_new_marks():
    students = copy.deepcopy(api.students)
    api.update_marks()
    for i in range(len(api.students)):
        if students[i].subjects != api.students[i].subjects:
            last_name = students[i].name.split(' ')[1]
            id = list(LAST_NAMES.keys())[list(LAST_NAMES.values()).index(last_name)]
            for j in range(len(students[i].subjects), len(api.students[i].subjects)):
                if api.students[i].subjects[j].marks != []:
                    await bot.send_message(id, f"У тебя новые оценки по предмету {api.students[i].subjects[j].name}: {api.students[i].subjects[j].marks}")
        for j in range(len(students[i].subjects)):
            if students[i].subjects[j].marks != api.students[i].subjects[j].marks:
                last_name = students[i].name.split(' ')[1]
                id = list(LAST_NAMES.keys())[list(LAST_NAMES.values()).index(last_name)]
                for k in range(len(students[i].subjects[j].marks), len(api.students[i].subjects[j].marks)):
                    await bot.send_message(id, f"У тебя новые оценки по предмету {api.students[i].subjects[j].name}: {api.students[i].subjects[j].marks[len(students[i].subjects[j].marks):len(api.students[i].subjects[j].marks)]}")

async def scheduler():
    aioschedule.every(10).minutes.do(send_if_new_marks)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)

async def on_startup(_):
    asyncio.create_task(scheduler())

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
