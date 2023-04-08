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
    author: str
    title: str
    book_genres: list
    img_src: str
    comments_texts: list


def get_arguments():
    parser = argparse.ArgumentParser(
        description="Script downloads books from https://tululu.org"
    )
    parser.add_argument("start_id", help="this is start book id", type=int)
    parser.add_argument("end_id", help="this is end book id", type=int)
    return parser.parse_args()


def parse_book_page(soup) -> Book:
    title_author_h = soup.find("td", class_="ow_px_td")\
        .find("div", id="content")\
        .find("h1")
    title, author = (
        sanitize_filename(text.strip())
        for text in title_author_h.text.split("::")
        )
    img_src = soup.find("div", class_="bookimage").find("a").find("img")["src"]
    comments_divs = soup.find_all("div", class_="texts")
    comments_texts = [
        comment_div.find("span").text for comment_div in comments_divs
        ]
    genres_as = soup.find("span", class_="d_book").find_all("a")
    book_genres = [genre_a.text for genre_a in genres_as]
    return Book(author, title, book_genres, img_src, comments_texts)


def download_book_commentaries(book: Book, book_index, file_directory):
    file_full_name = os.path.join(
        file_directory,
        f"{book_index}. {book.title}.txt"
    )
    with open(file_full_name, "w") as file:
        for comment_text in book.comments_texts:
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


def download_image(book: Book, response, book_full_url, file_directory):
    image_path = urljoin(book_full_url, book.img_src)
    logo_name = urlsplit(image_path).path.split("/")[-1]

    file_full_name = os.path.join(file_directory, logo_name)
    with open(file_full_name, "wb") as file:
        file.write(response.content)


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPErrorbook_response


def main(failed_attempts=False, start_id=0):
    book_txt_url = "https://tululu.org/txt.php"
    books_url = "https://tululu.org"
    file_directory = "./books"
    books_logo_directory = "./images"
    commentaries_directory = "./books_commentaries"
    if not failed_attempts:
        arguments = get_arguments()
        Path(file_directory).mkdir(parents=True, exist_ok=True)
        Path(books_logo_directory).mkdir(parents=True, exist_ok=True)
        Path(commentaries_directory).mkdir(parents=True, exist_ok=True)
        start_id = arguments.start_id
    for book_index in range(start_id, arguments.end_id):
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
                book_response,
                book_full_url,
                books_logo_directory
            )
            download_book_commentaries(
                book,
                book_index,
                commentaries_directory
            )
        except requests.HTTPError:
            print(f"book (id={book_index}) was not found")
        except requests.ConnectionError:
            if not failed_attempts:
                time_sleep = 0.05
            else:
                time_sleep = 0.5
            print("Connection error, trying to reconnect.")
            time.sleep(time_sleep)
            main(failed_attempts=True, start_id=book_index)


if __name__ == "__main__":
    main()
