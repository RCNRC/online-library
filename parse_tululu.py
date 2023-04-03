import requests
from pathlib import Path
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
import os
from urllib.parse import urljoin, urlsplit
import argparse
import time


def get_arguments():
    parser = argparse.ArgumentParser(
        description="Script downloads books from https://tululu.org"
    )
    parser.add_argument('start_id', help="this is start book id", type=int)
    parser.add_argument('end_id', help="this is end book id", type=int)
    return parser.parse_args()


def parse_book_page(soup):
    h_1 = soup.find("td", class_="ow_px_td")\
        .find("div", id="content")\
        .find("h1")
    author = sanitize_filename(h_1.text.split("::")[1].strip())
    img_src = soup.find("div", class_="bookimage").find("a").find("img")["src"]
    comments_divs = soup.find_all("div", class_="texts")
    comments_texts = []
    for comment_div in comments_divs:
        comments_texts.append(comment_div.find("span").text)
    book_dict = {
        "author": author,
        "title": get_book_title(soup),
        "genres": get_book_genre(soup),
        "img_src": img_src,
        "comments_texts": comments_texts,
    }
    return book_dict


def get_book_genre(soup):
    genres_as = soup.find("span", class_="d_book").find_all("a")
    book_genres = []
    for genre_a in genres_as:
        book_genres.append(genre_a.text)
    return book_genres


def get_book_title(soup):
    h_1 = soup.find("td", class_="ow_px_td")\
        .find("div", id="content")\
        .find("h1")
    title = sanitize_filename(h_1.text.split("::")[0].strip())
    return title


def download_book_commentaries(book_index, soup, book_name, file_directory):
    comments_texts = parse_book_page(soup)["comments_texts"]
    file_full_name = os.path.join(
        file_directory,
        f"{book_index}. {book_name}.txt"
    )
    with open(file_full_name, 'w') as file:
        for comment_text in comments_texts:
            file.write(f"{comment_text}\n")


def download_book(book_name, file_directory, book_index, book_txt_url):
    payload = {
        "id": f"{book_index}"
    }
    response = requests.get(book_txt_url, params=payload)
    response.raise_for_status()
    check_for_redirect(response)
    file_full_name = os.path.join(
        file_directory,
        f"{book_index}. {book_name}.txt"
    )
    with open(file_full_name, 'wb') as file:
        file.write(response.content)


def download_image(soup, response, book_full_url, file_directory):
    img_src = parse_book_page(soup)["img_src"]
    image_path = urljoin(book_full_url, img_src)
    logo_name = urlsplit(image_path).path.split("/")[-1]

    file_full_name = os.path.join(file_directory, logo_name)
    with open(file_full_name, 'wb') as file:
        file.write(response.content)


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def main(failed_attempts=False, start_id=0):
    arguments = get_arguments()
    book_txt_url = "https://tululu.org/txt.php"
    books_url = "https://tululu.org"
    file_directory = "./books"
    books_logo_directory = "./images"
    commentaries_directory = "./books_commentaries"
    Path(file_directory).mkdir(parents=True, exist_ok=True)
    Path(books_logo_directory).mkdir(parents=True, exist_ok=True)
    Path(commentaries_directory).mkdir(parents=True, exist_ok=True)
    start_id = arguments.start_id if not failed_attempts else start_id
    for book_index in range(start_id, arguments.end_id):
        try:
            book_full_url = f"{books_url}/b{book_index}/"
            book_response = requests.get(book_full_url)
            book_response.raise_for_status()
            check_for_redirect(book_response)
            soup = BeautifulSoup(book_response.text, "lxml")

            book_name = get_book_title(soup)
            download_book(
                book_name,
                file_directory,
                book_index,
                book_txt_url
            )
            download_image(
                soup,
                book_response,
                book_full_url,
                books_logo_directory
            )
            download_book_commentaries(
                book_index,
                soup,
                book_name,
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


if __name__ == '__main__':
    main()
