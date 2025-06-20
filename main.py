import argparse
import csv
import os
import re

from operator import itemgetter
from tabulate import tabulate


AGGREGATION_TYPE = ['avg', 'min', 'max']


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
       description='Скрипт анализа файла данных csv'
    )

    parser.add_argument(
        '--file',
        nargs='?',
        default=os.path.join(os.getcwd(), 'products.csv'),
        help='директория с файлом csv (по умолчанию - ПУТЬ_К_ПАПКЕ_СО_СКРИПТОМ/products.csv)'
    )

    parser.add_argument(
        '--where',
        nargs='?',
        help='Условия выборки: >, < или =, например "price>1000"'
    )

    parser.add_argument(
        '--aggregate',
        nargs='?',
        help='Условия аггрегации: с расчетом среднего (avg), минимального (min) и максимального (max) значения, '
             'например "price=avg" или "rating=max"'
    )

    parser.add_argument(
        '--order_by',
        nargs='?',
        help='Условия сортировки: asc (по возрастанию) или desc (по убыванию), '
             'например "price=asc" или "rating=desc"'
    )

    return parser.parse_args()


def check_args(parsed_args: argparse.Namespace) -> None:
    if not os.path.isfile(parsed_args.file):
        print(f'Файл {parsed_args.file} отсутствует. Продолжение невозможно. Проверьте путь к файлу и его имя.')
        exit()

    # Проверка условий выборки, аггрегации и прочих на корректность формата
    for arg_key, parsed_arg in vars(parsed_args).items():
        if arg_key in ('file', ):  # file не нужно проверять на формат
            continue

        if parsed_arg and not re.search(r'[=><]', parsed_arg):
            print(f'Неверно указаны условия выборки в `{parsed_arg}`.')
            exit()

        if arg_key == 'aggregate' and parsed_arg:  # возможные проверки формата аггрегации на данном этапе
            splited_aggregate = parsed_args.aggregate.split('=')
            general_error_phrase = f'Неверно указаны условия аггрегации в `{parsed_args.aggregate}`.'

            if len(splited_aggregate) != 2:
                print(f'{general_error_phrase} '
                      f'Формат "поле=тип_аггрегации {AGGREGATION_TYPE}"')
                exit()

            if not splited_aggregate[1] in AGGREGATION_TYPE:  # проверка типа аггрегации в числе доступных
                print(f'{general_error_phrase} '
                      f'Тип аггрегации {splited_aggregate[1]} отсутствует.')
                exit()

        if arg_key == 'order_by' and parsed_arg:  # возможные проверки формата сортировки на данном этапе
            splited_order_by = parsed_args.order_by.split('=')
            general_error_phrase = f'Неверно указаны условия сортировки в `{parsed_args.order_by}`.'

            if len(splited_order_by) != 2:
                print(f'{general_error_phrase} '
                      f'Формат "поле=тип_сортировки [asc или desc]')
                exit()

            if not splited_order_by[1] in ['asc', 'desc']:  # проверка типа сортировки в числе доступных
                print(f'{general_error_phrase} '
                      f'Тип сортировки {splited_order_by[1]} отсутствует.')
                exit()


def load_products(file_path: str) -> list[dict[str, str]]:
    products = []
    with open(file_path, newline='') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            products.append(row)
    return products


def determine_type(value: str) -> str:
    """Определяет тип значения: int, float или string."""
    try:
        int(value)
        return 'int'
    except ValueError:
        pass

    try:
        float(value)
        return 'float'
    except ValueError:
        pass

    return 'string'


def filter_products(
        products: list[dict[str, str]],
        filtered_field: str,
        filtered_value: str,
        sign: str,
) -> list[dict[str, str]]:
    filtered_products = []

    # Проверка наличия поля выборки
    if not products[0].get(filtered_field):
        print(f'Неверно указаны условия выборки `{filtered_field}{sign}{filtered_value}`. '
              f'Поле {filtered_field} отсутствует.')
        exit()

    # Проверка валидности знака и типа данных в поле выборки
    if sign != '==' and not products[0].get(filtered_field).replace('.', '', 1).isdigit():
        print(f'Неверно указаны условия выборки `{filtered_field}{sign}{filtered_value}`. '
              f'Поле {filtered_field} не является числовым.')
        exit()

    for product in products:
        if (determine_type(filtered_value) in ('float', 'int')
                and eval(f'float(product.get("{filtered_field}")){sign}float({filtered_value})')):
            filtered_products.append(product)

        if (determine_type(filtered_value) == 'string'
                and eval(f'product.get("{filtered_field}"){sign}"{filtered_value}"')):
            filtered_products.append(product)

    return filtered_products


def aggregate_products(
        filtered_products: list[dict[str, str]],
        aggregate_field: str,
        aggregate_type: str,
) -> float:
    general_error_phrase = f'Неверно указаны условия аггрегации в `{aggregate_field}={aggregate_type}`.'

    if not filtered_products[0].get(aggregate_field):
        print(f'{general_error_phrase} '
              f'Поле {aggregate_field} отсутствует.')
        exit()

    try:
        float(filtered_products[0].get(aggregate_field))
    except ValueError:
        print(f'{general_error_phrase} '
              f'Поле {aggregate_field} не является числовым.')
        exit()

    value = 0

    if aggregate_type == 'min':
        value = float(filtered_products[0].get(aggregate_field))
        for product in filtered_products:
            if float(product[aggregate_field]) < value:
                value = float(product.get(aggregate_field))

    elif aggregate_type == 'max':
        value = float(filtered_products[0].get(aggregate_field))
        for product in filtered_products:
            if float(product[aggregate_field]) > value:
                value = float(product.get(aggregate_field))

    elif aggregate_type == 'avg':
        pre_value = 0
        for product in filtered_products:
            pre_value += float(product.get(aggregate_field))
        value = pre_value / len(filtered_products)

    return round(value, 2)


def sort_products(filtered_products: list[dict[str, str]], order_field: str, order_by: str) -> list[dict[str, str]]:
    if not filtered_products[0].get(order_field):
        print(f'Неверно указаны условия выборки `{order_field}={order_by}`. '
              f'Поле {order_field} отсутствует.')
        exit()

    filtered_products = sorted(
        filtered_products,
        key=itemgetter(order_field),
        reverse=True if order_by == 'desc' else False,
    )
    return filtered_products


def main() -> None:

    parsed_args = parse_arguments()
    file_path = parsed_args.file
    check_args(parsed_args)
    products = load_products(file_path)

    if parsed_args.where:
        sign = re.search(r'[=><]', parsed_args.where).group()
        filtered_field, filtered_value = parsed_args.where.split(sign)

        if sign == '=':
            sign = '=='

        filtered_products = filter_products(products, filtered_field, filtered_value, sign)
        if not filtered_products:
            print('Ни один продукт не соответствует условиям выборки.')
            return
    else:
        filtered_products = products

    if not parsed_args.aggregate:  # если условия аггрегации не указаны - выводим таблицу и завершаем

        if parsed_args.order_by:
            order_field, order_by = parsed_args.order_by.split('=')
            filtered_products = sort_products(filtered_products, order_field, order_by)

        header = list(filtered_products[0].keys())
        rows = [x.values() for x in filtered_products]
        print(tabulate(rows, header, tablefmt="outline"))
        return

    aggregate_field, aggregate_type = parsed_args.aggregate.split('=')
    value = aggregate_products(filtered_products, aggregate_field, aggregate_type)

    print(tabulate([[value]], [aggregate_type], tablefmt="outline"))


if __name__ == '__main__':
    main()
