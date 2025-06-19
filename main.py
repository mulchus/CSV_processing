import argparse
import os
import csv
import re
from tabulate import tabulate


AGGREGATION_CONDITIONS = ['avg', 'min', 'max']


def parse_argements() -> argparse.Namespace:
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

    return parser.parse_args()


def check_args(parsed_args):
    if not os.path.isfile(parsed_args.file):
        exit(f'Файл {parsed_args.file} не найден. Продолжение невозможно. Проверьте путь к файлу и его имя.')

    # Проверка условий выборки, аггрегации и прочих на корректность формата
    for arg_key, parsed_arg in vars(parsed_args).items():
        if arg_key in ('file', ):  # file не нужно проверять на формат
            continue

        if parsed_arg and not re.search(r'[=><]', parsed_arg):
            exit(f'Неверно указаны условия выборки в `{parsed_arg}`.')

        if arg_key == 'aggregate' and parsed_arg:  # возможные проверки формата аггрегации на данном этапе
            splited_aggregate = parsed_args.aggregate.split('=')
            general_error_phrase = f'Неверно указаны условия аггрегации в `{parsed_args.aggregate}`.'

            if len(splited_aggregate) != 2:
                exit(f'{general_error_phrase} '
                     f'Формат "поле=тип_аггрегации ({AGGREGATION_CONDITIONS})"')

            if not splited_aggregate[1] in AGGREGATION_CONDITIONS:
                exit(f'{general_error_phrase} '
                     f'Условие аггрегации {splited_aggregate[1]} не найдено.')

    return parsed_args


def load_products(file_path):
    products = []
    with open(file_path, newline='') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            products.append(row)
    return products


def filter_products(products, parsed_args):
    filtered_products = []
    if parsed_args.where:
        sign = re.search(r'[=><]', parsed_args.where).group()
        splited_where = parsed_args.where.split(sign)

        if sign == '=':
            sign = '=='
        splited_where.append(sign)

        # Проверка наличия поля выборки
        if not products[0].get(splited_where[0]):
            exit(f'Неверно указаны условия выборки в `{parsed_args.where}`. '
                 f'Поле {splited_where[0]} не найдено.')

        # Проверка валидности знака и типа данных в поле выборки
        if sign != '==' and not products[0].get(splited_where[0]).replace('.', '', 1).isdigit():
            exit(f'Неверно указаны условия выборки в `{parsed_args.where}`. '
                 f'Поле {splited_where[0]} не является числом.')

        for product in products:
            if eval(f'float(product.get("{splited_where[0]}")){splited_where[2]}float({splited_where[1]})'):
                filtered_products.append(product)

    return filtered_products


def aggregate_products(filtered_products, aggregate_field, aggregate_type):
    general_error_phrase = f'Неверно указаны условия аггрегации в `{aggregate_field}={aggregate_type}`.'

    if not filtered_products[0].get(aggregate_field):
        exit(f'{general_error_phrase} '
             f'Поле {aggregate_field} не найдено.')

    try:
        float(filtered_products[0].get(aggregate_field))
    except ValueError:
        exit(f'{general_error_phrase} '
             f'Поле {aggregate_field} не является числом.')

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

    return value


def main():

    parsed_args = parse_argements()
    file_path = parsed_args.file
    check_args(parsed_args)
    products = load_products(file_path)

    if parsed_args.where:
        filtered_products = filter_products(products, parsed_args)
        if not filtered_products:
            exit('Ни один продукт не соответствует условиям выборки.')
    else:
        filtered_products = products

    if not parsed_args.aggregate:  # если условия аггрегации не указаны - выводим таблицу и завершаем
        header = list(filtered_products[0].keys())
        rows = [x.values() for x in filtered_products]
        exit(tabulate(rows, header, tablefmt="outline"))

    aggregate_field, aggregate_type = parsed_args.aggregate.split('=')
    value = aggregate_products(filtered_products, aggregate_field, aggregate_type)

    print(tabulate([[value]], [aggregate_type], tablefmt="outline"))


if __name__ == '__main__':
    main()
