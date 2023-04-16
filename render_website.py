from jinja2 import Environment, FileSystemLoader, select_autoescape
import json
from livereload import Server
from more_itertools import chunked
from pathlib import Path
from math import ceil


def form_index(pages_directory):
    with open("./books/books.json", "rb") as my_file:
        books_text = my_file.read()

    books = json.loads(books_text)

    books_in_row = 2
    books_on_page = 20
    raw_on_page = books_on_page//books_in_row
    separated_books = list(chunked(books, books_in_row))
    pages_count = ceil(len(separated_books)/raw_on_page)

    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    template = env.get_template('template.html')

    for page_number in range(pages_count):
        rendered_page = template.render(
            separated_books=separated_books[
                page_number*raw_on_page:(page_number+1)*raw_on_page
            ],
            pages=range(1, pages_count+1),
            current_page=page_number+1,
            last_page=pages_count,
        )

        with open(
            f"{pages_directory}/index{page_number+1}.html",
            "w",
            encoding="utf8"
        ) as file:
            file.write(rendered_page)
        print("HTML page was reformed.")


def main():
    pages_directory = "./pages"
    Path(pages_directory).mkdir(parents=True, exist_ok=True)
    form_index(pages_directory)
    server = Server()
    server.watch('template.html', form_index(pages_directory))
    server.serve(root='.')


if __name__ == "__main__":
    main()
