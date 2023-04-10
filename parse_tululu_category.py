from parse_tululu import check_for_redirect, parse_book_page, download_book,\
    download_image, download_book_commentaries

import requests
from bs4 import BeautifulSoup
import time
import json
from pathlib import Path
from dataclasses import asdict


def get_books_urls(books_base_url, category_url):
    books_urls = []
    for i in range(1, 5):
        response = requests.get(f"{category_url}/{i}")
        response.raise_for_status()
        check_for_redirect(response)
        soup = BeautifulSoup(response.text, "lxml")
        books_ids_selector = ".d_book .bookimage a"
        books_urls.extend([
            f"{books_base_url}{book_id['href']}"
            for book_id in soup.select(books_ids_selector)
        ])
    return books_urls


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
    while True:
        try:
            books_urls = get_books_urls(
                books_base_url=books_url,
                category_url=fantasy_category_url
            )
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
