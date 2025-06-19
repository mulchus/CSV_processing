# Скрипт анализа файла данных csv


### Как использовать?
Python должен быть уже установлен.
Рекомендуется использовать virtualenv/venv для изоляции проекта.
(https://docs.python.org/3/library/venv.html)  
Затем используйте pip для установки зависимостей:
```sh
pip install -r requirements.txt
```

### Настройка переменных окружения
Переменные окружения отсутствуют.

### Запуск скрипта
```sh
python main.py --file D:\Python\CSV_processing\products.csv --where "rating>4.0" --aggregate "rating>min"
```
```sh
options:
  -h, --help            show this help message and exit
  --file [FILE]         директория с файлом csv (по умолчанию - ПУТЬ_К_ПАПКЕ_СО_СКРИПТОМ/products.csv)
  --where [WHERE]       Условия выборки: >, < или =, например "price>1000"
  --aggregate [AGGREGATE]
                        Условия аггрегации: с расчетом среднего (avg), минимального (min) и максимального (max) значения, например "price=avg" или "rating=max"

```

### Результат работы на примере прилагаемого файла [products.csv](products.csv)

```sh
python main.py --where "price>500"
```
```sh
+------------------+---------+---------+----------+
| name             | brand   |   price |   rating |
+==================+=========+=========+==========+
| iphone 15 pro    | apple   |     999 |      4.9 |
| galaxy s23 ultra | samsung |    1199 |      4.8 |
| iphone 14        | apple   |     799 |      4.7 |
| galaxy z flip 5  | samsung |     999 |      4.6 |
| iphone 13 mini   | apple   |     599 |      4.5 |
+------------------+---------+---------+----------+
```

```sh
python main.py --where "price>500" --aggregate "price=avg"
```
```sh
+-------+
|   avg |
+=======+
|   919 |
+-------+
```

```sh
python main.py --where "price<500"
```
```sh
+---------------+---------+---------+----------+
| name          | brand   |   price |   rating |
+===============+=========+=========+==========+
| redmi note 12 | xiaomi  |     199 |      4.6 |
| galaxy a54    | samsung |     349 |      4.2 |
| poco x5 pro   | xiaomi  |     299 |      4.4 |
| iphone se     | apple   |     429 |      4.1 |
| redmi 10c     | xiaomi  |     149 |      4.1 |
+---------------+---------+---------+----------+
```

```sh
python main.py --where "price<500" --aggregate "rating=min"
```
```sh
+-------+
|   min |
+=======+
|   4.1 |
+-------+
```

```sh
python main.py --where "name>600"
```
```sh
Неверно указаны условия выборки `name>600`. Поле name не является числовым.
```

```sh
python main.py --where "price>500" --aggregate "price>avg"
```
```sh
Неверно указаны условия аггрегации в `price>avg`. Формат "поле=тип_аггрегации (['avg', 'min', 'max'])"
```

### Запуск тестов
При любом изменении кода обязательно проверяйте работу тестов и покрывайте новый код новыми тестами

```shell
pytest -s -vv tests.py
```

### Проверка покрытия кода тестами
```shell
pytest --cov=main --cov-report html tests.py      
```
Результат будет размещен в файле [index.html](htmlcov/index.html)


## Цель проекта
Тестовое задание на собес, [ссылка](https://docs.google.com/document/d/1nraUeVCkbsyvjNvMAWAwgrn7w3DXHsQf15QS1eZ2F1U/edit?tab=t.0)
