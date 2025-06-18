import argparse
import os
import csv
import re
from tabulate import tabulate


def contains_special_character(pattern, input_string):
    match = re.search(pattern, input_string)
    # print(f'MATCH {match.span()[0]}')
    return match is not None


def check_arg_format(parsed_arg):
    # print(parsed_arg)
    if parsed_arg and not contains_special_character(r'[=><]', parsed_arg):
        exit(f'Неверно указаны условия выборки в `{parsed_arg}`.')


def main():
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

    parsed_args = parser.parse_args()
    print(parsed_args)

    if not os.path.isfile(parsed_args.file):
        exit(f'Файл {parsed_args.file} не найден. Продолжение невозможно. Проверьте путь к файлу и его имя.')

    products = []
    with open(parsed_args.file, newline='') as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=',')
        for row in csvreader:
            products.append(row)

    print(list(products[0].keys()))


    # Gроверка условий выборки, аггрегации и прочих на корректность формата
    print(vars(parsed_args).pop('file'))
    for parsed_arg in vars(parsed_args).values():
        check_arg_format(parsed_arg)

    print(parsed_args)

    if parsed_args.aggregate:
        splited_aggregate = parsed_args.aggregate.split(re.search(r'[=><]', parsed_args.aggregate).group())
        print(splited_aggregate)

    filtered_products = []
    if parsed_args.where:
        sign = re.search(r'[=><]', parsed_args.where).group()
        splited_where = parsed_args.where.split(sign)

        if sign == '=':
            sign = '=='
        splited_where.append(sign)
        print(splited_where)

        # Проверка наличия поля выборки
        if not products[0].get(splited_where[0]):
            exit(f'Неверно указаны условия выборки в `{parsed_args.where}`. Поле {splited_where[0]} не найдено.')

        # Проверка валидности знака и типа данных в поле выборки
        if sign != '==' and not products[0].get(splited_where[0]).replace('.','',1).isdigit():
            exit(f'Неверно указаны условия выборки в `{parsed_args.where}`. Поле {splited_where[0]} не является числом.')

        for product in products:
            if isinstance(splited_where[1], float):
                condition = eval(f'product.get("{splited_where[0]}"){splited_where[2]}float({splited_where[1]})')
            elif splited_where[1].isdigit():
                condition = eval(f'int(product.get("{splited_where[0]}")){splited_where[2]}int({splited_where[1]})')
            else:
                condition = eval(f'product.get("{splited_where[0]}"){splited_where[2]}"{splited_where[1]}"')

            if condition:
                filtered_products.append(product)


    print(filtered_products)

    # print(tabulate(filtered_products.items(), headers=['NAME', 'VALUE'], tablefmt="grid"))

    header = list(filtered_products[0].keys())
    rows = [x.values() for x in filtered_products]
    print(tabulate(rows, header, tablefmt="outline"))


    # TODO: Реализовать аггрегацию

    # TODO: Реализовать сортировку

if __name__ == '__main__':
    main()
