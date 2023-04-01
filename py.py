import requests
from pathlib import Path


def download_book(book_index, book_url, file_directory):
    payload = {
        "id": f"{book_index}"
    }
    response = requests.get(book_url, params=payload)
    response.raise_for_status()

    file_name = str(file_directory) + "/" + str(book_index) + ".txt"
    with open(file_name, 'wb') as file:
        file.write(response.content)


def main():
    book_url = "https://tululu.org/txt.php"
    file_directory= './books'
    Path("./books").mkdir(parents=True, exist_ok=True)
    for i in range(10):
        download_book(i+32160, book_url, file_directory)


if __name__ == '__main__':
    main()
