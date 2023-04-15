import requests
from pathlib import Path
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
import os
from urllib.parse import urljoin, urlsplit
import argparse
import time
from dataclasses import dataclass


@dataclass
class Book:
    title: str
    author: str
    img_src: str
    img_alt: str
    comments: list
    genres: list


def get_arguments():
    parser = argparse.ArgumentParser(
        description="Script downloads books from https://tululu.org"
    )
    parser.add_argument("start_id", help="this is start book id", type=int)
    parser.add_argument("end_id", help="this is end book id", type=int)
    return parser.parse_args()


def parse_book_page(soup) -> Book:
    title_author_h_selector = ".ow_px_td div[id=content] h1"
    title, author = (
        sanitize_filename(text.strip())
        for text in soup.select_one(title_author_h_selector).text.split("::")
        )
    img_selector = ".bookimage a img"
    img_src = soup.select_one(img_selector)["src"]
    img_alt = soup.select_one(img_selector)["alt"]
    comments_spans_selector = ".texts span"
    comments = [
        comment_span.text
        for comment_span in soup.select(comments_spans_selector)
    ]
    genres_as_selector = "span.d_book a"
    genres = [genre_a.text for genre_a in soup.select(genres_as_selector)]
    return Book(title, author, img_src, img_alt, comments, genres)


def download_book_commentaries(book: Book, book_index, file_directory):
    file_full_name = os.path.join(
        file_directory,
        f"{book_index}. {book.title}.txt"
    )
    with open(file_full_name, "w") as file:
        for comment_text in book.comments:
            file.write(f"{comment_text}\n")


def download_book(book: Book, file_directory, book_index, book_txt_url):
    payload = {
        "id": f"{book_index}"
    }
    response = requests.get(book_txt_url, params=payload)
    response.raise_for_status()
    check_for_redirect(response)
    file_full_name = os.path.join(
        file_directory,
        f"{book_index}. {book.title}.txt"
    )
    with open(file_full_name, "wb") as file:
        file.write(response.content)


def download_image(book: Book, book_full_url, file_directory):
    image_path = urljoin(book_full_url, book.img_src)
    logo_name = urlsplit(image_path).path.split("/")[-1]

    response = requests.get(image_path)
    response.raise_for_status()
    check_for_redirect(response)

    file_full_name = os.path.join(file_directory, logo_name)
    with open(file_full_name, "wb") as file:
        file.write(response.content)


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def main():
    book_txt_url = "https://tululu.org/txt.php"
    books_url = "https://tululu.org"
    file_directory = "./books"
    books_logo_directory = "./images"
    commentaries_directory = "./books_commentaries"
    arguments = get_arguments()
    Path(file_directory).mkdir(parents=True, exist_ok=True)
    Path(books_logo_directory).mkdir(parents=True, exist_ok=True)
    Path(commentaries_directory).mkdir(parents=True, exist_ok=True)
    failed_attempts = False
    for book_index in range(arguments.start_id, arguments.end_id):
        while True:
            try:
                book_full_url = f"{books_url}/b{book_index}/"
                book_response = requests.get(book_full_url)
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
                    book_full_url,
                    books_logo_directory
                )
                download_book_commentaries(
                    book,
                    book_index,
                    commentaries_directory
                )
                failed_attempts = False
                break
            except requests.HTTPError:
                print(f"book (id={book_index}) was not found")
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


if __name__ == "__main__":
    main()
