from parse_tululu import check_for_redirect, parse_book_page, download_book,\
    download_image, download_book_commentaries

import requests
from bs4 import BeautifulSoup
import time
import json
from pathlib import Path
from dataclasses import asdict
import argparse


def get_last_page_number(category_url):
    response = requests.get(f"{category_url}/1")
    response.raise_for_status()
    check_for_redirect(response)
    soup = BeautifulSoup(response.text, "lxml")
    available_pages = "a.npage"
    return int(soup.select(available_pages)[-1].text)


def get_arguments(last_page):
    parser = argparse.ArgumentParser(
        description="Script downloads books from https://tululu.org"
    )
    parser.add_argument(
        "--dest_folder",
        required=False,
        help="directory for results of downloading",
        type=str,
        default=".",
    )
    parser.add_argument(
        "--start_page",
        required=False,
        help="this is start book id",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--end_page",
        required=False,
        help="this is end book id",
        type=int,
        default=last_page,
    )
    parser.add_argument(
        "--skip_imgs",
        required=False,
        help="if 'True' then dont download books images",
        action='store_true',
    )
    parser.add_argument(
        "--skip_txt",
        required=False,
        help="if 'True' then dont download books texts",
        action='store_true',
    )
    parser.add_argument(
        "--json_path",
        required=False,
        help="directory for results in json format",
        type=str,
        default=".",
    )
    return parser.parse_args()


def get_books_urls_on_page(page, books_base_url, category_url):
    response = requests.get(f"{category_url}/{page}")
    response.raise_for_status()
    check_for_redirect(response)
    soup = BeautifulSoup(response.text, "lxml")
    books_ids_selector = ".d_book .bookimage a"
    return [
        f"{books_base_url}{book_id['href']}"
        for book_id in soup.select(books_ids_selector)
    ]


def main():
    fantasy_category_url = "https://tululu.org/l55/"
    books_url = "https://tululu.org"
    last_page = get_last_page_number(fantasy_category_url)
    arguments = get_arguments(last_page)
    json_reults_directory = arguments.json_path
    if json_reults_directory != ".":
        Path(json_reults_directory).mkdir(parents=True, exist_ok=True)
    if not arguments.skip_txt:
        book_txt_url = "https://tululu.org/txt.php"
        file_directory = f"{arguments.dest_folder}/books"
        Path(file_directory).mkdir(parents=True, exist_ok=True)
    if not arguments.skip_imgs:
        books_logo_directory = f"{arguments.dest_folder}/images"
        Path(books_logo_directory).mkdir(parents=True, exist_ok=True)
    commentaries_directory = f"{arguments.dest_folder}/books_commentaries"
    Path(commentaries_directory).mkdir(parents=True, exist_ok=True)
    failed_attempts = False
    books_urls = []
    for page in range(arguments.start_page, arguments.end_page):
        while True:
            try:
                books_urls.extend(get_books_urls_on_page(
                    page,
                    books_base_url=books_url,
                    category_url=fantasy_category_url,
                ))
                failed_attempts = False
                break
            except requests.HTTPError:
                print("Redirect for books category")
                failed_attempts = False
                break
            except requests.ConnectionError:
                if not failed_attempts:
                    time_sleep = 0.05
                    failed_attempts = True
                else:
                    time_sleep = 0.5
                print("Connection error, trying to reconnect.")
                time.sleep(time_sleep)

    books = []
    for book_index, book_url in enumerate(books_urls):
        while True:
            try:
                book_response = requests.get(book_url)
                book_response.raise_for_status()
                check_for_redirect(book_response)
                soup = BeautifulSoup(book_response.text, "lxml")
                book = parse_book_page(soup)

                if not arguments.skip_txt:
                    download_book(
                        book,
                        file_directory,
                        book_index,
                        book_txt_url
                    )
                if not arguments.skip_imgs:
                    download_image(
                        book,
                        book_url,
                        books_logo_directory
                    )
                download_book_commentaries(
                    book,
                    book_index,
                    commentaries_directory
                )
                book_for_json = asdict(book)
                book_for_json["img_src"] = f"{arguments.dest_folder}/images/"\
                    f"{book_for_json['img_src'].split('/')[-1]}"
                book_for_json["book_path"] = f"{arguments.dest_folder}/"\
                    f"books/{book_index}. "\
                    f"{book_for_json['title']}.txt"
                books.append(book_for_json)
                failed_attempts = False
                break
            except requests.HTTPError:
                print(f"book (url={book_url}, id={book_index}) was not found")
                failed_attempts = False
                break
            except requests.ConnectionError:
                if not failed_attempts:
                    time_sleep = 0.05
                    failed_attempts = True
                else:
                    time_sleep = 0.5
                print("Connection error, trying to reconnect.")
                time.sleep(time_sleep)

    with open(f"{json_reults_directory}/books.json", "w") as file:
        json.dump(books, file, ensure_ascii=False)


if __name__ == "__main__":
    main()
