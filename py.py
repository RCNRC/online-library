import requests
from pathlib import Path
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
import os


def get_book_name(index, book_url):
    
    book_full_url = f"{book_url}{index}/"
    response = requests.get(book_full_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    h1 = soup.find("td", class_="ow_px_td").find("div", id="content").find("h1")
    title, author = h1.text.split("::")
    title, author = sanitize_filename(title.strip()), sanitize_filename(author.strip())
    return title


def check_for_redirect(response):
    for history_point in response.history:
        if history_point.status_code == 302:
            raise requests.HTTPError


def download_book(index, book_index, book_txt_url, book_url, file_directory):
    payload = {
        "id": f"{book_index}"
    }
    response = requests.get(book_txt_url, params=payload)
    response.raise_for_status()
    check_for_redirect(response)
    index += 1
    file_name = f"{index}. {get_book_name(book_index, book_url)}.txt"

    file_full_name = os.path.join(file_directory, file_name)
    with open(file_full_name, 'wb') as file:
        file.write(response.content)
    
    return index


def main():
    book_txt_url = "https://tululu.org/txt.php"
    book_url = "https://tululu.org/b"
    file_directory = './books'
    Path("./books").mkdir(parents=True, exist_ok=True)
    index = 0
    for book_index in range(1, 10):
        try:
            index = download_book(index, book_index, book_txt_url, book_url, file_directory)
        except requests.HTTPError:
            print(f"book (id={index}) was not found")


if __name__ == '__main__':
    main()
