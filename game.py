import requests
from bs4 import BeautifulSoup
from googletrans import Translator

# Инициализируем переводчик
translator = Translator()

def translate_to_russian(text):
    try:
        translation = translator.translate(text, src='en', dest='ru')
        return translation.text
    except Exception as e:
        print(f"Ошибка перевода: {e}")
        return text  # Возвращаем оригинальный текст, если перевод не удался

def get_english_words():
    url = "https://randomword.com/"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверяем на ошибки HTTP

        soup = BeautifulSoup(response.content, "html.parser")
        english_word = soup.find("div", id="random_word").text.strip()
        word_definition = soup.find("div", id="random_word_definition").text.strip()

        # Переводим на русский
        russian_word = translate_to_russian(english_word)
        russian_definition = translate_to_russian(word_definition)

        return {
            "english_word": english_word,
            "russian_word": russian_word,
            "russian_definition": russian_definition
        }

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к сайту: {e}")
        return None
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return None

def word_game():
    print("Добро пожаловать в игру 'Угадай слово'!")
    print("Вам будет дано определение слова на русском, попробуйте угадать само слово.\n")

    while True:
        word_data = get_english_words()
        if not word_data:
            print("Не удалось получить слово. Попробуем ещё раз...")
            continue

        print(f"Определение: {word_data['russian_definition']}")
        user_input = input("Что это за слово? ").strip().lower()

        # Сравниваем с обоими вариантами (английское и русское слово)
        if user_input == word_data['english_word'].lower() or user_input == word_data['russian_word'].lower():
            print("Правильно! 🎉")
        else:
            print(f"Неверно. Правильный ответ: {word_data['russian_word']} ({word_data['english_word']})")

        play_again = input("\nХотите сыграть ещё раз? (y/n): ").strip().lower()
        if play_again != 'y':
            print("Спасибо за игру! До встречи!")
            break

if __name__ == "__main__":
    word_game()