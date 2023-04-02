import requests
from pathlib import Path
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
import os
from urllib.parse import urljoin, urlsplit


def parse_book_page(soup):
    h_1 = soup.find("td", class_="ow_px_td")\
        .find("div", id="content")\
        .find("h1")
    author = sanitize_filename(h_1.text.split("::")[1].strip())
    book_dict = {
        "author": author,
        "title": get_book_title(soup),
        "genres": get_book_genre(soup),
    }
    print(book_dict)
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


def download_book_commentaries(index, soup, book_name, file_directory):
    comments_divs = soup.find_all("div", class_="texts")
    file_full_name = os.path.join(file_directory, f"{index}. {book_name}.txt")
    with open(file_full_name, 'w') as file:
        for comment_div in comments_divs:
            comment = comment_div.find("span")
            file.write(f"{comment.text}\n")


def download_book(index, response, book_name, file_directory):
    file_full_name = os.path.join(file_directory, f"{index}. {book_name}.txt")
    with open(file_full_name, 'wb') as file:
        file.write(response.content)


def download_image(soup, response, book_full_url, file_directory):
    img_src = soup.find("div", class_="bookimage").find("a").find("img")["src"]
    image_path = urljoin(book_full_url, img_src)
    logo_name = urlsplit(image_path).path.split("/")[-1]
    
    file_full_name = os.path.join(file_directory, logo_name)
    with open(file_full_name, 'wb') as file:
        file.write(response.content)


def check_for_redirect(response):
    for history_point in response.history:
        if history_point.status_code == 302:
            raise requests.HTTPError


def get_book_txt_response(book_index, book_txt_url):
    payload = {
        "id": f"{book_index}"
    }
    response = requests.get(book_txt_url, params=payload)
    response.raise_for_status()
    check_for_redirect(response)
    return response


def get_book_parameters(books_url, index):
    book_full_url = f"{books_url}/b{index}/"
    response = requests.get(book_full_url)
    response.raise_for_status()
    check_for_redirect(response)
    soup = BeautifulSoup(response.text, "lxml")
    return soup, response, book_full_url


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
            soup, book_response, book_full_url = get_book_parameters(
                books_url,
                book_index
            )
            book_name = get_book_title(soup)
            book_txt_response = get_book_txt_response(book_index, book_txt_url)
            download_book(index, book_txt_response, book_name, file_directory)
            download_image(
                soup,
                book_response,
                book_full_url,
                books_logo_directory
            )
            download_book_commentaries(
                index,
                soup,
                book_name,
                commentaries_directory
            )
            parse_book_page(soup)
            index += 1
        except requests.HTTPError:
            print(f"book (id={index}) was not found")


if __name__ == '__main__':
    main()
