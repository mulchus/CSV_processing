import argparse
import csv
from io import StringIO
from operator import itemgetter
from unittest.mock import patch

import pytest

from main import check_args, load_products, parse_arguments, filter_products, aggregate_products, sort_products


csv_rows = [
    {'name': 'iphone 15 pro', 'brand': 'apple', 'price': 999, 'rating': 4.9},
    {'name': 'redmi note 12', 'brand': 'xiaomi', 'price': 199, 'rating': 4.6},
    {'name': 'poco x5 pro', 'brand': 'xiaomi', 'price': 299, 'rating': 4.4},
]


@pytest.fixture
def temp_csv(tmpdir):
    csv_file = tmpdir.join("temporary.csv")
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['name', 'brand', 'price', 'rating'])
        writer.writeheader()
        writer.writerows(csv_rows)
    return str(csv_file)


def test_load_products(temp_csv):
    products = load_products(temp_csv)
    assert len(products) == 3
    assert products[0] == {'name': 'iphone 15 pro', 'brand': 'apple', 'price': 999, 'rating': 4.9}
    assert products[1] == {'name': 'redmi note 12', 'brand': 'xiaomi', 'price': 199, 'rating': 4.6}
    assert products[2] == {'name': 'poco x5 pro', 'brand': 'xiaomi', 'price': 299, 'rating': 4.4}


def test_argparser_good_args():
    test_args = [
        'main.py', '--file', '123.csv', '--where', 'name=poco', '--aggregate', 'price=avg', '--order', 'price=asc'
    ]
    with patch('sys.argv', test_args):
        parse_arguments()


@pytest.mark.parametrize(
    "test_args",
    [
        (['main.py', '--fake_file', '123.csv', '--where', 'name>poco', '--aggregate', 'price-avg']),
        (['main.py', '--file', '123.csv', '--fake_where', 'name>poco', '--aggregate', 'price-avg']),
        (['main.py', '--file', '123.csv', '--where', 'name>poco', '--fake_aggregate', 'price-avg']),
    ]
)
def test_argparser_bad_args_names(test_args):
    with patch('sys.argv', test_args):
        with pytest.raises(SystemExit):
            parse_arguments()


@pytest.mark.parametrize(
    "filtered_field, filtered_value, sign",
    [
        ('name', 'poco', '=='),  # '==' потому что так передается в функцию для подстановки в eval вычисление
        ('brand', 'xiaomi', '=='),
    ]
)
def test_filter_good_where_values(temp_csv, filtered_field, filtered_value, sign):
    products = load_products(temp_csv)
    filter_products(products, filtered_field, filtered_value, sign)


@pytest.mark.parametrize(
    "filtered_field, filtered_value, sign",
    [
        ('name', 'poco', '>'),
        ('name', 'poco', '<'),
        ('brand', 'xiaomi', '<'),
        ('brand', 'xiaomi', '>'),
    ]
)
def test_filter_bad_where_values(temp_csv, filtered_field, filtered_value, sign):
    products = load_products(temp_csv)
    with pytest.raises(SystemExit):
        filter_products(products, filtered_field, filtered_value, sign)


@pytest.mark.parametrize(
    "parsed_args",
    [
        (argparse.Namespace(file="temporary.csv", whre='name=poco', aggregate='rating=min')),
        (argparse.Namespace(file="temporary.csv", whre='brand=xiaomi', aggregate='rating=avg')),
    ]
)
def test_check_args_good_values(temp_csv, parsed_args):
    parsed_args.file = temp_csv
    check_args(parsed_args)


@pytest.mark.parametrize(
    "parsed_args, error_message",
    [
        (argparse.Namespace(file="temporary.csv", whre='name-poco', aggregate='rating=min'),
         "Неверно указаны условия выборки в `name-poco`"),
        (argparse.Namespace(file="temporary.csv", whre='brand*xiaomi', aggregate='rating=min'),
         "Неверно указаны условия выборки в `brand*xiaomi`"),
        (argparse.Namespace(file="temporary.csv", whre='brand=xiaomi', aggregate='rating=fake_min'),
         "Неверно указаны условия аггрегации в `rating=fake_min`"),
        (argparse.Namespace(file="temporary.csv", whre='brand=xiaomi', aggregate='rating>min'),
         "Неверно указаны условия аггрегации в `rating>min`"),
        (argparse.Namespace(file="temporary.csv", whre='brand=xiaomi', order_by='rating=fake_asc'),
         "Неверно указаны условия сортировки в `rating=fake_asc`"),
        (argparse.Namespace(file="temporary.csv", whre='brand=xiaomi', order_by='rating>desc'),
         "Неверно указаны условия сортировки в `rating>desc`"),
    ]
)
def test_check_args_bad_values(temp_csv, parsed_args, error_message):
    with pytest.raises(SystemExit):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            parsed_args.file = temp_csv
            check_args(parsed_args)
    assert error_message in fake_out.getvalue()


@pytest.mark.parametrize(
    "parsed_args, error_message",
    [
        (argparse.Namespace(file="temporary.csv", whre='name=poco', aggregate='rating=min'),
         "Файл temporary.csv отсутствует"),
    ]
)
def test_check_args_bad_file_path(temp_csv, parsed_args, error_message):
    with pytest.raises(SystemExit):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            # parsed_args.file = temp_csv
            check_args(parsed_args)
    assert error_message in fake_out.getvalue()


@pytest.mark.parametrize(
    "filtered_field, filtered_value, sign, filter_result",
    [
        ('name', 'poco', '==', []),
        ('name', 'iphone 15 pro', '==', [{'name': 'iphone 15 pro', 'brand': 'apple', 'price': 999, 'rating': 4.9}]),
        ('brand', 'xiaomi', '==', [{'name': 'redmi note 12', 'brand': 'xiaomi', 'price': 199, 'rating': 4.6},
                                   {'name': 'poco x5 pro', 'brand': 'xiaomi', 'price': 299, 'rating': 4.4}]),
        ('brand', 'nokia', '==', []),
        ('price', '200', '>', [{'name': 'iphone 15 pro', 'brand': 'apple', 'price': 999, 'rating': 4.9},
                               {'name': 'poco x5 pro', 'brand': 'xiaomi', 'price': 299, 'rating': 4.4}]),
        ('rating', '4.7', '<', [{'name': 'redmi note 12', 'brand': 'xiaomi', 'price': 199, 'rating': 4.6},
                                {'name': 'poco x5 pro', 'brand': 'xiaomi', 'price': 299, 'rating': 4.4}]),
    ]
)
def test_filter(temp_csv, filtered_field, filtered_value, sign, filter_result):
    products = load_products(temp_csv)
    filtered_products = filter_products(products, filtered_field, filtered_value, sign)
    assert filtered_products == filter_result


@pytest.mark.parametrize(
    "field_to_order, order_by, order_by_result",
    [
        ('name', 'asc', sorted(csv_rows.copy(), key=itemgetter('name'))),
        ('name', 'desc', sorted(csv_rows.copy(), key=itemgetter('name'), reverse=True)),
        ('brand', 'asc', sorted(csv_rows.copy(), key=itemgetter('brand'))),
        ('brand', 'desc', sorted(csv_rows.copy(), key=itemgetter('brand'), reverse=True)),
        ('price', 'asc', sorted(csv_rows.copy(), key=itemgetter('price'))),
        ('price', 'desc', sorted(csv_rows.copy(), key=itemgetter('price'), reverse=True)),
        ('rating', 'asc', sorted(csv_rows.copy(), key=itemgetter('rating'))),
        ('rating', 'desc', sorted(csv_rows.copy(), key=itemgetter('rating'), reverse=True)),
    ]
)
def test_order_by(temp_csv, field_to_order, order_by, order_by_result):
    products = load_products(temp_csv)
    sorted_products = sort_products(products, field_to_order, order_by)
    assert sorted_products == order_by_result


@pytest.mark.parametrize(
    "aggregate_field, aggregate_type, agregate_result",
    [
        ('price', 'max', 999.0),
        ('price', 'min', 199.0),
        ('price', 'avg', 499.0),
        ('rating', 'max', 4.9),
        ('rating', 'min', 4.4),
        ('rating', 'avg', 4.63),
    ]
)
def test_aggregate(temp_csv, aggregate_field, aggregate_type, agregate_result):
    products = load_products(temp_csv)
    aggregated_products = aggregate_products(products, aggregate_field, aggregate_type)
    assert aggregated_products == agregate_result


@pytest.mark.parametrize(
    "aggregate_field, aggregate_type, error_message",
    [
        ('fake_price', 'max', "Поле fake_price отсутствует"),
        ('name', 'min', "Поле name не является числовым."),
    ]
)
def test_aggregate_bad_fields(temp_csv, aggregate_field, aggregate_type, error_message):
    with pytest.raises(SystemExit):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            products = load_products(temp_csv)
            aggregate_products(products, aggregate_field, aggregate_type)
    assert error_message in fake_out.getvalue()


@pytest.mark.parametrize(
    "filtered_field, filtered_value, sign, error_message",
    [
        ('fake_name', 'poco', '==', 'Поле fake_name отсутствует'),
    ]
)
def test_filter_bad_fields(temp_csv, filtered_field, filtered_value, sign, error_message):
    with pytest.raises(SystemExit):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            products = load_products(temp_csv)
            filter_products(products, filtered_field, filtered_value, sign)
    assert error_message in fake_out.getvalue()


@pytest.mark.parametrize(
    "field_to_order, order_by, error_message",
    [
        ('fake_name', 'desc', 'Поле fake_name отсутствует'),
    ]
)
def test_order_by_bad_fields(temp_csv, field_to_order, order_by, error_message):
    with pytest.raises(SystemExit):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            products = load_products(temp_csv)
            sort_products(products, field_to_order, order_by)
    assert error_message in fake_out.getvalue()
