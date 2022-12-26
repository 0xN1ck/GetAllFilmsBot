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


async def get_translates(callback: CallbackQuery, kp_id: str):
    CDN = VideoCDN(callback.bot.data['config'].token_cdn)
    data = CDN.get_movies(ParamsContent(query=kp_id, field=Field.KINOPOISK_ID))
    return data.data[0].translations


async def get_info_film(token_kp, kp_id: str):
    api_client = KinopoiskApiClient(token_kp)
    request = FilmRequest(int(kp_id))
    response = api_client.films.send_film_request(request)
    name = response.film.name_ru
    photo = response.film.poster_url_preview
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
        'description': description,
        'rating_kp': rating_kp,
        'rating_imdb': rating_imdb
    }


    # await message.answer(f'Название : <b>{movie.ru_title}</b>\n'
    #                      f'Ссылка для просмотра : {movie.iframe_src}',
    #                      )
