# online-library

Это скрипт скачивающий книги с [книжного сайта](https://tululu.org), их обложки и комментарии.

## Подготовка к использованию

Скачать гит репозиторий.

Требуется [Python](https://www.python.org/downloads/) версии 3.7 или выше и установленный [pip](https://pip.pypa.io/en/stable/getting-started/). Для установки необходимых зависимостей в корне репозитория используйте команду:  
1. Для Unix/macOs:
```commandline
python -m pip install -r requirements.txt
```
2. Для Windows:
```commandline
py -m pip download --destination-directory DIR -r requirements.txt
```

## Запуск

Скрипт запускается как `python3` скрипт с двумя обязательными параметрами:
1. `--start_id` - ID книги, с которой начнётся скачивание.
2. `--end_id` - ID книги, до которой будет происходить скачивание.

При запуске скачивает книги в папку `books`, комментарии к книгам в папку `books_commentaries`, иззображения обложек книг в `images`. В случае если по очередной книге не будет найдено файлов, в консоль выведется соответствующее оповещение.

Пример запуска:
```comandline
> python3 parse_tululu.py 10 20
book (id=14) was not found
book (id=16) was not found
book (id=17) was not found
```
