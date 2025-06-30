# from selenium import webdriver  # Для управления браузером и навигации
# from selenium.webdriver.chrome.service import Service  # Настройка сервиса ChromeDriver
# from webdriver_manager.chrome import ChromeDriverManager  # Автоматическая установка ChromeDriver
# from selenium.webdriver.common.by import By  # Поиск элементов на странице по селекторам
# from selenium.webdriver.common.keys import Keys  # Симуляция нажатия клавиш (например, Enter)
# from selenium.webdriver.chrome.options import Options  # Настройка опций Chrome (размер окна, etc)
# import time  # Задержки для ожидания загрузки страниц
# import urllib.parse  # Добавлен для декодирования URL
# import textwrap  # Добавлен для обрезки строк
#
#
# def init_driver():
#     chrome_options = Options()
#     chrome_options.add_argument("--start-maximized")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     service = Service(ChromeDriverManager().install())
#     return webdriver.Chrome(service=service, options=chrome_options)
#
# def search_wikipedia(driver, query):
#     driver.get("https://ru.wikipedia.org/wiki/Заглавная_страница")
#     time.sleep(2)
#     search_box = driver.find_element(By.ID, "searchInput")
#     search_box.clear()
#     search_box.send_keys(query)
#     search_box.send_keys(Keys.RETURN)
#     time.sleep(2)
#
#     try:
#         first_result = driver.find_element(By.CSS_SELECTOR, ".mw-search-result-heading a")
#         first_result.click()
#         time.sleep(2)
#     except:
#         print("Результаты поиска не найдены.")
#         driver.quit()
#         exit()
#
#
#
# def list_paragraphs(driver):
#     try:
#         paragraphs = driver.find_elements(By.TAG_NAME, 'p')
#         for i, p in enumerate(paragraphs):
#             # Обрезка текста до 100 символов в строке
#             wrapped_text = textwrap.wrap(p.text, width=125, break_long_words=False)
#             print(f"\nПараграф {i+1}:")
#             for line in wrapped_text:
#                 print(line)
#             choice = input("Нажмите Enter для следующего параграфа или введите 'меню' для возврата: ")
#             if choice.lower() == 'меню':
#                 break
#         print("Конец просмотра параграфов.")
#     except Exception as e:
#         print(f"Ошибка при чтении параграфов: {str(e)}")
#
# def navigate_to_link(driver, history, current_index):
#     try:
#         content = driver.find_element(By.CSS_SELECTOR, "#mw-content-text > div.mw-parser-output")
#         links = content.find_elements(By.TAG_NAME, "a")
#
#         internal_links = []
#         for link in links:
#             href = link.get_attribute("href")
#             if href and "/wiki/" in href and "#" not in href:
#                 internal_links.append(link)
#
#         if not internal_links:
#             print("Нет доступных внутренних ссылок.")
#             return
#
#         page_size = 25
#         current_page = 0
#         total_pages = (len(internal_links) + page_size - 1) // page_size
#
#         while True:
#             start = current_page * page_size
#             end = start + page_size
#             displayed_links = internal_links[start:end]
#
#             print(f"\nСтраница {current_page + 1}/{total_pages}")
#             for idx, link in enumerate(displayed_links, 1):
#                 # Декодируем название ссылки
#                 title = urllib.parse.unquote(link.get_attribute("title"))
#                 print(f"{idx}. {title}")
#
#             print("\nДоступные действия:")
#             print("n - следующая страница")
#             print("p - предыдущая страница")
#             print("назад - вернуться в меню")
#
#             action = input("Выберите действие или номер ссылки: ").lower()
#
#             if action == 'n' and current_page < total_pages - 1:
#                 current_page += 1
#             elif action == 'p' and current_page > 0:
#                 current_page -= 1
#             elif action == 'назад':
#                 return
#             else:
#                 try:
#                     num = int(action) - 1
#                     if 0 <= num < len(displayed_links):
#                         selected_link = displayed_links[num]
#                         selected_link.click()
#                         time.sleep(2)
#                         # Добавляем декодированное название в историю
#                         title = urllib.parse.unquote(driver.current_url.split('/')[-1].replace('_', ' '))
#                         history.append(title)
#                         current_index = len(history) - 1
#                         return
#                     else:
#                         print("Неверный номер.")
#                 except:
#                     print("Неверный ввод.")
#     except Exception as e:
#         print(f"Ошибка при переходе: {str(e)}")
#
# def main():
#     driver = init_driver()
#     query = input("Введите ваш запрос: ")
#     search_wikipedia(driver, query)
#
#     # Инициализируем историю с декодированным названием
#     history = [urllib.parse.unquote(driver.current_url.split('/')[-1].replace('_', ' '))]
#     current_index = 0
#
#     while True:
#         print("\nТекущая страница:", driver.title)
#         print("История:", " → ".join(history[:current_index+1]))
#
#         print("\nВыберите действие:")
#         print("1. Листать параграфы")
#         print("2. Перейти по ссылке")
#         print("0. Вернуться назад")
#         print("3. Выйти")
#         choice = input("Ваш выбор: ")
#
#         try:
#             if choice == '1':
#                 list_paragraphs(driver)
#             elif choice == '2':
#                 navigate_to_link(driver, history, current_index)
#                 current_index = len(history) - 1
#             elif choice == '0':
#                 if current_index > 0:
#                     current_index -= 1
#                     # Возвращаемся по истории
#                     driver.get(f"https://ru.wikipedia.org/wiki/{urllib.parse.quote(history[current_index].replace('  ', '_'))}")
#                     print("Возвращаемся назад.")
#                 else:
#                     print("Вы находитесь на начальной странице.")
#             elif choice == '3':
#                 driver.quit()
#                 print("Программа завершена.")
#                 break
#             else:
#                 print("Неверный выбор.")
#         except Exception as e:
#             print(f"Ошибка: {str(e)}")
#
# if __name__ == "__main__":
#     main()
#
#
#
#
# # import requests
# # import pprint
# #
# # # Настройка pretty printer для красивого вывода JSON
# # pp = pprint.PrettyPrinter(indent=2)
# #
# # print("=" * 50)
# # print("Задание 1: Получение данных")
# # print("=" * 50)
# #
# # # 1. Получение данных с GitHub API
# # def task1():
# #     url = "https://api.github.com/search/repositories"
# #     params = {
# #         'q': 'html',  # поиск репозиториев с кодом html
# #         'sort': 'stars',
# #         'order': 'desc'
# #     }
# #
# #     response = requests.get(url, params=params)
# #
# #     # 3. Печать статус-кода
# #     print(f"Статус-код ответа: {response.status_code}")
# #
# #     # 4. Печать содержимого в формате JSON
# #     if response.ok:
# #         data = response.json()
# #         print(f"\nКоличество репозиториев с использованием html: {data['total_count']}")
# #         print("\nРезультаты поиска репозиториев:")
# #         pp.pprint(data)
# #     else:
# #         print("Ошибка при выполнении запроса")
# #
# #
# #
# # task1()
# #
# # print("\n" + "=" * 50)
# # print("Задание 2: Параметры запроса")
# # print("=" * 50)
# #
# # # 2. Фильтрация данных через URL-параметры
# # def task2():
# #     url = "https://jsonplaceholder.typicode.com/posts"
# #     params = {
# #         'userId': 1  # фильтрация по userId
# #     }
# #
# #     response = requests.get(url, params=params)
# #
# #     if response.ok:
# #         posts = response.json()
# #         print(f"Найдено {len(posts)} записей для userId=1:")
# #         for post in posts[:3]:  # выводим первые 3 записи для краткости
# #             print(f"\nЗапись #{post['id']}:")
# #             print(f"Title: {post['title']}")
# #             print(f"Body: {post['body']}")
# #     else:
# #         print("Ошибка при выполнении запроса")
# #
# # task2()
# #
# # print("\n" + "=" * 50)
# # print("Задание 3: Отправка данных")
# # print("=" * 50)
# #
# # # 3. Отправка POST-запроса
# # def task3():
# #     url = "https://jsonplaceholder.typicode.com/posts"
# #     data = {
# #         'title': 'foo',
# #         'body': 'bar',
# #         'userId': 1
# #     }
# #
# #     response = requests.post(url, json=data)
# #
# #     # 4. Печать статус-кода и ответа
# #     print(f"Статус-код ответа: {response.status_code}")
# #
# #     if response.ok:
# #         print("\nСозданная запись:")
# #         pp.pprint(response.json())
# #     else:
# #         print("Ошибка при выполнении запроса")
# #
# # task3()
