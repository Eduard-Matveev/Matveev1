import requests
import pandas as pd
from retry import retry


HEADERS = {

}
CATALOG_URL = 'https://static-basket-01.wbbasket.ru/vol0/data/main-menu-ru-ru-v2.json' # Ссылка на список каталогов


def get_catalogs_wb() -> dict:
   #получаем полный каталог Wildberries 
    return requests.get(CATALOG_URL, headers=HEADERS).json()


def get_data_category(catalogs_wb: dict) -> list:
   #сбор данных категорий из каталога Wildberries 
    catalog_data = []
    if isinstance(catalogs_wb, dict) and 'childs' not in catalogs_wb:
        catalog_data.append({
            'name': f"{catalogs_wb['name']}",
            'shard': catalogs_wb.get('shard', None),
            'url': catalogs_wb['url'],
            'query': catalogs_wb.get('query', None)
        })
    elif isinstance(catalogs_wb, dict): #Добавляем подкатегории
        catalog_data.extend(get_data_category(catalogs_wb['childs']))
    else:
        for child in catalogs_wb:
            catalog_data.extend(get_data_category(child))
    return catalog_data


def search_category_in_catalog(url: str, catalog_list: list) -> dict:
   #проверка пользовательской ссылки на наличии в каталоге 
    for catalog in catalog_list:
        if catalog['url'] == url.split('https://www.wildberries.ru')[-1]:
            print(f'Найдено: {catalog["name"]}')
            return catalog


def get_data_from_json(json_file: dict) -> list:
   #извлекаем из json данные 
    data_list = []
    for data in json_file['data']['products']:
        data_list.append({
            'id': data.get('id'),
            'Название': data.get('name'),
            'Стоимость': int(data.get("priceU") / 100),
            'Стоимость со скидкой': int(data.get('salePriceU') / 100),
            'Скидка': data.get('sale'),
            'Бренд': data.get('brand'),
            'Рейтинг': data.get('rating'),
            'Продавец': data.get('supplier'),
            'Рейтинг продавца': data.get('supplierRating'),
            'Кол-во отзывов': data.get('feedbacks'),
            'Рейтинг отзывов': data.get('reviewRating'),
            'Промо текст карточки': data.get('promoTextCard'),
            'Промо текст категории': data.get('promoTextCat'),
            'Ссылка': f'https://www.wildberries.ru/catalog/{data.get("id")}/detail.aspx?targetUrl=BP'
        })
    return data_list


@retry(Exception, tries=-1, delay=0)
def scrap_page(page: int, shard: str, query: str, low_price: int, top_price: int, discount: int = None) -> dict:
   #Сбор данных со страниц 
    url = f'https://catalog.wb.ru/catalog/{shard}/catalog?appType=1&curr=rub' \
          f'&dest=-1257786' \
          f'&locale=ru' \
          f'&page={page}' \
          f'&priceU={low_price * 100};{top_price * 100}' \
          f'&sort=popular&spp=0' \
          f'&{query}' \
          f'&discount={discount}'

    r = requests.get(url, headers=HEADERS)
    print(f'[+] Страница {page}')
    return r.json()


def save_excel(data: list, filename: str):
   #сохранение результата в excel файл 
    df = pd.DataFrame(data)
    writer = pd.ExcelWriter(f'{filename}.xlsx')
    df.to_excel(writer, sheet_name='data', index=False)
    # размеры каждого столбца в таблице
    writer.sheets['data'].set_column(0, 1, width=10)
    writer.sheets['data'].set_column(1, 2, width=65)
    writer.sheets['data'].set_column(2, 3, width=10)
    writer.sheets['data'].set_column(3, 4, width=21)
    writer.sheets['data'].set_column(4, 5, width=7)
    writer.sheets['data'].set_column(5, 6, width=20)
    writer.sheets['data'].set_column(6, 7, width=8)
    writer.sheets['data'].set_column(7, 8, width=25)
    writer.sheets['data'].set_column(8, 9, width=17)
    writer.sheets['data'].set_column(9, 10, width=15)
    writer.sheets['data'].set_column(10, 11, width=16)
    writer.sheets['data'].set_column(11, 12, width=21)
    writer.sheets['data'].set_column(12, 13, width=21)
    writer.sheets['data'].set_column(13, 14, width=67)
    writer.close()
    print(f'Результаты сохранены в {filename}.xlsx\n')


def parser(url: str, low_price: int = 1, top_price: int = 1000000, discount: int = 0):
   #основная функция 
    # получаем данные по заданному каталогу
    catalog_data = get_data_category(get_catalogs_wb())
    try:
        # поиск введенной категории в общем каталоге
        category = search_category_in_catalog(url=url, catalog_list=catalog_data)
        data_list = []
        for page in range(1, 5):  # вб отдает 50 страниц товара
            data = scrap_page(
                page=page, #Страница
                shard=category['shard'], #Название категории
                query=category['query'], #Id категории
                low_price=low_price, #Нижний порог цены
                top_price=top_price, #Верхний порог цены
                discount=discount) #Скидка
            if len(get_data_from_json(data)) > 0:
                data_list.extend(get_data_from_json(data))
            else:
                break
        print(f'Собрано: {len(data_list)} товаров.')
        # сохранение найденных данных
        save_excel(data_list, f'{category["name"]}От{low_price}До{top_price}')
        print(f'Ссылка для проверки: {url}?priceU={low_price * 100};{top_price * 100}&discount={discount}')
    except TypeError:
        print('Ошибка! Возможно не верно указан раздел. Удалите все доп фильтры с ссылки')
    except PermissionError:
        print('Ошибка! Вы забыли закрыть созданный ранее excel файл. Закройте и повторите попытку')


if __name__ == '__main__':
    url = 'https://www.wildberries.ru/catalog/obuv/muzhskaya/botinki-i-polubotinki'  # ВСТАВЛЯЕМ ЛЮБУЮ ССЫЛКУ КАТЕГОРИИ
    low_price = 1000  # Фильтр по минимальной цене
    top_price = 10000  # Фильтр по максимальной цене
    discount = 10  # Фильтр по наличию скидки (указанное число и больше)

    
    parser(url=url, low_price=low_price, top_price=top_price, discount=discount)
