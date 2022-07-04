## ControlProjectTelegramBot
***

Notification of changes in the status of "Yandex Practical" projects. Designed for students of the "Yandex Practical" course Python-developer

### Prerequisites for using the product

* Knowledge about:
  * Python
  * Packages of Python:
    * logging
    * telegram
  * Availability: 
    * Python version 3, 
    * Telegram bot (created in [BotFather](https://t.me/botfather))
    * Python packages from ```requirements.txt```
### Getting started
Installation from source (requires git):
```shell
$ git clone https://github.com/p0lzi/homework_bot.git
$ cd homework_bot
```
### How to use
* Create a virtual environment
```shell 
python -m venv venv
```
* Installing packages from the ```requirements.txt``` file
```shell
pip install -r requirements.txt
```
* Create file .env
* Added variables in .env:
  * ```TOKEN``` (Get [@BotFather](https://t.me/botfather) -> /mybots -> **@Your_Name_Bot'** -> API Token)
  * ```MY_CHAT_ID``` (Get [@userinfobot](https://t.me/userinfobot) -> in the **id** field)
  * ```PRACTICUM_TOKEN``` (Get [oauth.yandex.ru](https://oauth.yandex.ru/verification_code#access_token=AQAAAAA4rreHAAYckWgS-ZjgRURpjRWzn0pe3m8&token_type=bearer&expires_in=2255894))
* Run python script
```shell
python homework.py
```
