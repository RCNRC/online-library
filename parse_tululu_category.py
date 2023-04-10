from parse_tululu import check_for_redirect, parse_book_page, download_book,\
    download_image, download_book_commentaries

import requests
from bs4 import BeautifulSoup
import time
import json
from pathlib import Path
from dataclasses import asdict
import argparse


def get_arguments(category_url):
    response = requests.get(f"{category_url}/1")
    response.raise_for_status()
    check_for_redirect(response)
    soup = BeautifulSoup(response.text, "lxml")
    available_pages = "a.npage"
    last_page = int(soup.select(available_pages)[-1].text)

    parser = argparse.ArgumentParser(
        description="Script downloads books from https://tululu.org"
    )
    parser.add_argument(
        "start_page",
        help="this is start book id",
        type=int,
        default=0,
    )
    parser.add_argument(
        "end_page",
        help="this is end book id",
        type=int,
        default=last_page,
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
    book_txt_url = "https://tululu.org/txt.php"
    file_directory = "./books"
    books_logo_directory = "./images"
    commentaries_directory = "./books_commentaries"
    Path(file_directory).mkdir(parents=True, exist_ok=True)
    Path(books_logo_directory).mkdir(parents=True, exist_ok=True)
    Path(commentaries_directory).mkdir(parents=True, exist_ok=True)
    fantasy_category_url = "https://tululu.org/l55/"
    books_url = "https://tululu.org"
    failed_attempts = False
    arguments = get_arguments(fantasy_category_url)
    books_urls = []
    for page in range(arguments.start_page, arguments.end_page):
        while True:
            try:
                books_urls.extend(get_books_urls_on_page(
                    page,
                    books_base_url=books_url,
                    category_url=fantasy_category_url,
                ))
                print(books_urls)
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

                download_book(
                    book,
                    file_directory,
                    book_index,
                    book_txt_url
                )
                download_image(
                    book,
                    book_response,
                    book_url,
                    books_logo_directory
                )
                download_book_commentaries(
                    book,
                    book_index,
                    commentaries_directory
                )
                book = asdict(book)
                book["img_src"] = f"images/{book['img_src'].split('/')[-1]}"
                book["book_path"] = f"books/{book_index}. {book['title']}.txt"
                books.append(book)
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

    capitals_json = json.dumps(books, ensure_ascii=False).encode('utf8')
    with open("books.json", "w") as my_file:
        my_file.write(capitals_json.decode())


if __name__ == "__main__":
    main()
