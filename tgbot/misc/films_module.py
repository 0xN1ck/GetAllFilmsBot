from typing import List
from videocdn_tv import VideoCDN, ParamsContent
from videocdn_tv.type.field import Field
from kinopoisk_unofficial.kinopoisk_api_client import KinopoiskApiClient
from kinopoisk_unofficial.request.films.film_request import FilmRequest
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import Dispatcher
from typing import Union
from aiogram.dispatcher import FSMContext


async def get_films(message: Union[CallbackQuery, Message], state: FSMContext, current_page=1, **kwargs):
    CDN = VideoCDN(message.bot.data['config'].token_cdn)
    async with state.proxy() as data:
        query = data['search']
    # total_films = CDN.get_movies(ParamsContent(query=query)).total
    data = CDN.get_movies(ParamsContent(query=query, page=current_page))
    return data
    # elif isinstance(message, CallbackQuery):
    #     data = CDN.get_movies(ParamsContent(query=query))
    #     return data.data


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


# async def get_qualities(callback: CallbackQuery, kp_id: str, translation_id):
#     CDN = VideoCDN(callback.bot.data['config'].token_cdn)
#     data = CDN.get_movies(ParamsContent(query=kp_id, field=Field.KINOPOISK_ID, translation=int(translation_id)))
#     for i in data.data[0].media:
#         print(i.translation_id, translation_id)
#         if i.translation_id is int(translation_id):
#             print(i)
