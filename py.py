import requests
from pathlib import Path
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
import os
from urllib.parse import urljoin, urlsplit


def get_book_genre(response):
    soup = BeautifulSoup(response.text, "lxml")
    genres_as = soup.find("span", class_="d_book").find_all("a")
    book_genres = []
    for genre_a in genres_as:
        book_genres.append(genre_a.text)
    print(book_genres)


def get_book_commentaries(response, book_name, file_directory):
    soup = BeautifulSoup(response.text, "lxml")
    comments_divs = soup.find_all("div", class_="texts")
    file_full_name = os.path.join(file_directory, book_name)
    with open(file_full_name, 'w') as file:
        for comment_div in comments_divs:
            comment = comment_div.find("span")
            file.write(f"{comment.text}\n")


def download_image(response, book_full_url, file_directory):
    soup = BeautifulSoup(response.text, "lxml")
    img_src = soup.find("div", class_="bookimage").find("a").find("img")["src"]
    image_path = urljoin(book_full_url, img_src)
    logo_name = urlsplit(image_path).path.split("/")[-1]
    
    file_full_name = os.path.join(file_directory, logo_name)
    with open(file_full_name, 'wb') as file:
        file.write(response.content)


def get_book_name(index, response):
    soup = BeautifulSoup(response.text, "lxml")
    h_1 = soup.find("td", class_="ow_px_td")\
        .find("div", id="content")\
        .find("h1")
    title, author = h_1.text.split("::")
    title, author = sanitize_filename(title.strip()), sanitize_filename(author.strip())
    return f"{index}. {title}.txt"


def check_for_redirect(response):
    for history_point in response.history:
        if history_point.status_code == 302:
            raise requests.HTTPError


def download_book(response, book_name, file_directory):
    file_full_name = os.path.join(file_directory, book_name)
    with open(file_full_name, 'wb') as file:
        file.write(response.content)


def get_book_txt_response(book_index, book_txt_url):
    payload = {
        "id": f"{book_index}"
    }
    response = requests.get(book_txt_url, params=payload)
    response.raise_for_status()
    check_for_redirect(response)
    return response


def get_book_response(books_url, index):
    book_full_url = f"{books_url}/b{index}/"
    response = requests.get(book_full_url)
    response.raise_for_status()
    check_for_redirect(response)
    return response, book_full_url


def main():
    book_txt_url = "https://tululu.org/txt.php"
    books_url = "https://tululu.org"
    file_directory = "./books"
    books_logo_directory = "./images"
    commentaries_directory = "./books_commentaries"
    Path(file_directory).mkdir(parents=True, exist_ok=True)
    Path(books_logo_directory).mkdir(parents=True, exist_ok=True)
    Path(commentaries_directory).mkdir(parents=True, exist_ok=True)
    index = 0
    for book_index in range(1, 10):
        try:
            book_response, book_full_url = get_book_response(books_url, book_index)
            book_name = get_book_name(index, book_response)
            book_txt_response = get_book_txt_response(book_index, book_txt_url)
            download_book(book_txt_response, book_name, file_directory)
            download_image(book_response, book_full_url, books_logo_directory)
            get_book_commentaries(book_response, book_name, commentaries_directory)
            get_book_genre(book_response)
            index += 1
        except requests.HTTPError:
            print(f"book (id={index}) was not found")


if __name__ == '__main__':
    main()
