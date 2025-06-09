import requests
import pprint

# Настройка pretty printer для красивого вывода JSON
pp = pprint.PrettyPrinter(indent=2)

print("=" * 50)
print("Задание 1: Получение данных")
print("=" * 50)

# 1. Получение данных с GitHub API
def task1():
    url = "https://api.github.com/search/repositories"
    params = {
        'q': 'html',  # поиск репозиториев с кодом html
        'sort': 'stars',
        'order': 'desc'
    }

    response = requests.get(url, params=params)

    # 3. Печать статус-кода
    print(f"Статус-код ответа: {response.status_code}")

    # 4. Печать содержимого в формате JSON
    if response.ok:
        data = response.json()
        print(f"\nКоличество репозиториев с использованием html: {data['total_count']}")
        print("\nРезультаты поиска репозиториев:")
        pp.pprint(data)
    else:
        print("Ошибка при выполнении запроса")



task1()

print("\n" + "=" * 50)
print("Задание 2: Параметры запроса")
print("=" * 50)

# 2. Фильтрация данных через URL-параметры
def task2():
    url = "https://jsonplaceholder.typicode.com/posts"
    params = {
        'userId': 1  # фильтрация по userId
    }

    response = requests.get(url, params=params)

    if response.ok:
        posts = response.json()
        print(f"Найдено {len(posts)} записей для userId=1:")
        for post in posts[:3]:  # выводим первые 3 записи для краткости
            print(f"\nЗапись #{post['id']}:")
            print(f"Title: {post['title']}")
            print(f"Body: {post['body']}")
    else:
        print("Ошибка при выполнении запроса")

task2()

print("\n" + "=" * 50)
print("Задание 3: Отправка данных")
print("=" * 50)

# 3. Отправка POST-запроса
def task3():
    url = "https://jsonplaceholder.typicode.com/posts"
    data = {
        'title': 'foo',
        'body': 'bar',
        'userId': 1
    }

    response = requests.post(url, json=data)

    # 4. Печать статус-кода и ответа
    print(f"Статус-код ответа: {response.status_code}")

    if response.ok:
        print("\nСозданная запись:")
        pp.pprint(response.json())
    else:
        print("Ошибка при выполнении запроса")

task3()
