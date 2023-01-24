from typing import List
from videocdn_tv import VideoCDN, ParamsContent
from videocdn_tv.type.field import Field
from kinopoisk_unofficial.kinopoisk_api_client import KinopoiskApiClient
from kinopoisk_unofficial.request.films.film_request import FilmRequest
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import Dispatcher
from typing import Union
from aiogram.dispatcher import FSMContext
from bs4 import BeautifulSoup
import requests, re


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
        description = description[0:930]+'...'
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
