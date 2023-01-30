import asyncio
import io
import json
import re

import aiogram
import requests
from typing import Union

from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery
from bs4 import BeautifulSoup
from kinopoisk_unofficial.kinopoisk_api_client import KinopoiskApiClient
from kinopoisk_unofficial.request.films.film_request import FilmRequest
from tqdm import tqdm
from videocdn_tv import VideoCDN, ParamsContent
from videocdn_tv.type.field import Field
from videoprops import get_video_properties


async def get_films(message: Union[CallbackQuery, Message], state: FSMContext, current_page=1, **kwargs):
    CDN = VideoCDN(message.bot.data['config'].token_cdn)
    async with state.proxy() as data:
        query = data['search']
    data = CDN.get_movies(ParamsContent(query=query, page=current_page))
    return data


async def get_movies(callback: CallbackQuery, kp_id: str):
    CDN = VideoCDN(callback.bot.data['config'].token_cdn)
    data = CDN.get_movies(ParamsContent(query=kp_id, field=Field.KINOPOISK_ID))
    return data.data[0].media


async def get_info_film(token_kp, kp_id: str):
    api_client = KinopoiskApiClient(token_kp)
    request = FilmRequest(int(kp_id))
    response = api_client.films.send_film_request(request)
    name = response.film.name_ru
    photo = response.film.poster_url_preview
    year = response.film.year
    duration = response.film.film_length
    genres = response.film.genres
    description = response.film.description
    if description is None:
        description = 'Описание отсутствует'
    elif len(description) > 930:
        description = description[0:930] + '...'
    rating_kp = response.film.rating_kinopoisk
    rating_imdb = response.film.rating_imdb
    return {
        'name': name,
        'photo': photo,
        "year": year,
        "duration": duration,
        "genres": genres,
        'description': description,
        'rating_kp': rating_kp,
        'rating_imdb': rating_imdb
    }


async def get_url_for_film(url: str, translation_id: int, quality: int):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    input_ = soup.find('input', id="files")
    value = input_.get('value')
    regexp_tr_id = f'"{str(translation_id)}":"' + r'(.+?)' + r'"'
    found = re.search(regexp_tr_id, value).group(1)
    link = re.split(r'_\d+.mp4', found.split(f'[{str(quality)}p]')[1])[0] + f'_{str(quality)}.mp4'
    link_utf = 'https:/' + link[3:].replace('\\/', '/').encode('utf-8').decode('unicode-escape')
    return link_utf


def download_film(callback: CallbackQuery, url: str, path: str, mes: Message, loop: asyncio.ProactorEventLoop,
                  bot: aiogram.bot.bot.Bot):
    # with open(path, "wb") as video:
    response = requests.get(url, stream=True)
    total_size_in_bytes = int(response.headers.get('content-length', 0))
    block_size = 1024
    percent_total = io.StringIO()
    percent_current = 10
    progress_bar = tqdm(file=percent_total, total=total_size_in_bytes, unit='iB', unit_scale=True,
                        mininterval=0.1)
    with open(path, 'wb') as file:
        for data in response.iter_content(block_size):
            percent_total.truncate(0)
            percent_total.seek(0)
            progress_bar.update(len(data))
            file.write(data)
            if int(round(progress_bar.last_print_n / total_size_in_bytes * 100)) >= percent_current:
                correctable_slice = percent_total.getvalue().split('|')[1]
                result = percent_total.getvalue().replace(correctable_slice,
                                                          re.sub(r'\d', '#', correctable_slice)).strip()
                name = callback.message.caption.split("\n")[0].split(":")[-1].strip()
                quality = callback.data.split(':')[-1]
                translate_id = callback.data.split(':')[-2]
                translate: str
                with open('tgbot\\translation.json', encoding='utf-8') as json_file:
                    data = json.load(json_file)
                for i in data['data']:
                    if i['id'] == int(translate_id):
                        translate = f"{i['shorter_title']}"
                loop.run_until_complete(
                    bot.edit_message_text(chat_id=mes.chat.id, message_id=mes.message_id,
                                          text=f"🎬 <b>Фильм:</b> <i>{name}</i>\n"
                                               f"<b>Перевод:</b> <i>{translate}</i>\n"
                                               f"<b>Качество:</b> <i>{quality}p</i>\n"
                                               f"Скачан на сервер в объеме:\n"
                                               f"{result.replace('<', ' ').split('[A')[0]}"))
                percent_current += 10
    progress_bar.close()
    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        print("ERROR, something went wrong")


def send_film(callback: CallbackQuery, path: str, loop: asyncio.ProactorEventLoop, bot: aiogram.bot.bot.Bot,
              chat_id: int):
    with open(path, "rb") as video:
        # thumb = await callback.bot.get_file(callback.message.photo[2].file_id)
        name = callback.message.caption.split("\n")[0].split(":")[-1].strip()
        duration = int(re.findall('\\d+', callback.message.caption.split("\n")[2])[0]) * 60
        props = get_video_properties(path)
        width = int(props['width'])
        height = int(props['height'])
        loop.run_until_complete(
            bot.send_video(chat_id=chat_id,
                           video=video,
                           duration=duration,
                           caption=f"{name}",
                           # thumb=open(thumb.file_path, 'rb'),
                           width=width,
                           height=height,
                           supports_streaming=True,
                           ))
