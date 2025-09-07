# Описание

# Парсер интернет-магазина Alkoteka

Scrapy-парсер для сбора данных о товарах с сайта alkoteka.com. Парсер получает полную информацию о товарах, включая цены, наличие, описания и характеристики.


## Функциональность
  - Сбор данных из карточек товаров.
  - Сохранение результатов в JSON-формате.
  - Поддержка региона (Краснодар по умолчанию).

## Технологии
  - **Python 3.10**
  - **Scrapy 2.12.0**

## Установка
1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/SergeyKurilko/alkotekaParser.git](https://github.com/winreit/scrapy
   ```
2. Перейдите в каталог alkotekaParser
   ```bash
   cd alkoteka_parser
   ```
3. Создайте виртуальное окружение и активируйте его:
  
   Для macOS/Linux
   ```bash
   python3 -m venv venv
   source venv/bin/activate 
   ```
   Для Windows
   ```bash
   python -m venv myenv
   myenv\Scripts\activate
   ```
   
6. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
7. Настройте URL адреса для парсинга:
   - Перейти в каталог `alkotekaParser/alkoteka_parser/spiders`
   - Открыть `alkoteka_spyder.py`
   - В классе AlkotekaDetailSpider найдите атрибут START_URLS и добавьте в список необходимые URL.

## Использование
Запустите парсер командной:
   ```bash
   scrapy crawl alkoteka_spider -O result.json
   ```

после выполениния команды появится вайл result.json с записанными данными
