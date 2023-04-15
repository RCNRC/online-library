from http.server import HTTPServer, SimpleHTTPRequestHandler

from jinja2 import Environment, FileSystemLoader, select_autoescape
import json
from livereload import Server
from more_itertools import chunked


def form_index():
    with open("./books/books.json", "r") as my_file:
        books_text = my_file.read()

    books = json.loads(books_text)
    separated_books = list(chunked(books, 2))
    print(separated_books[0])

    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    template = env.get_template('template.html')

    rendered_page = template.render(
        separated_books=separated_books
    )

    with open('index.html', 'w', encoding="utf8") as file:
        file.write(rendered_page)


def main():
    form_index()
    server = Server()
    server.watch('template.html', form_index)
    server.serve(root='.')
    #server = HTTPServer(('0.0.0.0', 8000), SimpleHTTPRequestHandler)
    #server.serve_forever()


if __name__ == "__main__":
    main()
