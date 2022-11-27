import telebot, os
from dotenv import load_dotenv


def main():
    print(f'Hi')
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    bot = telebot.TeleBot(os.environ.get("TOKEN"))
    print(bot)



if __name__ == '__main__':
    main()

