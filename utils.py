from flask import (
    request,
    session,
    jsonify,
)
from database.database_functions import (
    get_last_user_word,
    insert_into_user_words,
    get_user,
    insert_into_user_data,
    get_user_data,
    insert_into_logs,
)
import random

JWT_PAYLOAD = "jwt_payload"

bigwords = set()
dictionaryItems = set()
with open("dictionary.txt", "r") as f:
    dictionaryItems = set(f.read().lower().split("\n"))
    for items in dictionaryItems:
        if len(items) == 6:
            for i in items:
                if i <= "a" or i >= "z":
                    break
            else:
                bigwords.add(items)


def get_freq(word):
    all_freq = {}
    for i in word:
        if i in all_freq:
            all_freq[i] += 1
        else:
            all_freq[i] = 1
    return all_freq


def get_new_word():
    return random.sample(bigwords, 1)[0].upper()


def is_possible(og_word, word):
    print(og_word, word)
    if word.lower() not in dictionaryItems:
        print("not in dictionary")
        return "not in dictionary"
    og_freq = get_freq(og_word)
    for ch, val in get_freq(word).items():
        if ch not in og_freq:
            return "invalid"
        if val > og_freq[ch]:
            return "invalid"
    return "valid"


def shuffle_word(word):
    str_var = list(word)
    random.shuffle(str_var)
    return "  ".join(str_var)


def handle_commands(command):
    command = command.lower()

    if command in ["/new", "/skip"]:
        new_word = get_new_word()
        session["current_ans"] = []
        insert_into_user_words(get_user(session[JWT_PAYLOAD]["name"])[0][0], new_word)
        new_word = shuffle_word(new_word).upper()
        session["current_word"] = new_word
        return ""
    elif command == "/start":
        word = get_last_user_word(get_user(session[JWT_PAYLOAD]["name"])[0][0])
        session["current_ans"] = []
        session["score"] = 0
        if word == ():
            word = get_new_word()

            insert_into_user_words(get_user(session[JWT_PAYLOAD]["name"])[0][0], word)
        else:
            word = word[0][0]

        session["current_word"] = word.upper()
        return ""

    elif command == "/shuffle":
        word = (
            session["current_word"]
            if "current_word" in session
            else get_last_user_word(get_user(session[JWT_PAYLOAD]["name"])[0][0])[0][0]
        )
        word = shuffle_word(word).upper()
        session["current_word"] = word
        return "Your reshuffled word is " + word
    elif command == "/show":
        if "current_word" in session:
            return ""
        else:
            return get_last_user_word(get_user(session[JWT_PAYLOAD]["name"])[0][0])[0][
                0
            ]

    else:
        return "Wrong Command"


def get_user_words(email):

    data = get_user_data(get_user(email)[0][0])
    final_data = {}
    for user_word in data:
        if user_word["word"] in final_data:
            final_data[user_word["word"]] = (
                final_data[user_word["word"]] + ", " + user_word["input_word"]
            )
        else:
            final_data[user_word["word"]] = user_word["input_word"]
    return final_data


def conversation_log(func):
    """
    decorator to log conversations for a user
    :return: None
    """

    def wrapper(*args, **kwargs):
        if JWT_PAYLOAD in session and func.__name__ != "send_text":
            insert_into_logs(session[JWT_PAYLOAD]["name"], request.form["text"])
        elif func.__name__ == "send_text":
            insert_into_logs(session[JWT_PAYLOAD]["name"], args[0], True)
        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__
    return wrapper


@conversation_log
def send_text(text):

    return jsonify(text)


def split_text(text):
    return text.lower().replace(" ", "").split(",")


def add_score(is_proper):
    if "score" not in session:
        session["score"] = 0
    if is_proper == "valid":
        session["score"] += 1


def handle_input(message):

    try:
        response = {}
        if message.startswith("/"):

            response["text"] = handle_commands(message)

        else:

            og_word = get_last_user_word(get_user(session[JWT_PAYLOAD]["name"])[0][0])[
                0
            ][0]
            word = message.upper()
            if word not in session["current_ans"]:
                session["current_ans"].append(word)
                is_proper = is_possible(og_word, word.upper())
                add_score(is_proper)
                if is_proper == "valid":
                    insert_into_user_data(
                        get_user(session[JWT_PAYLOAD]["name"])[0][0], og_word, word
                    )
                    response["text"] = "valid"
                else:
                    response["text"] = "invalid"
            else:
                response["text"] = ""

        word = session["current_word"] if "current_word" in session else ""

        response["word"] = word
        response["score"] = session["score"]
        print(message, response["text"])
        return response

    except Exception as e:
        response["text"] = "Error " + str(e) + "</br>Try /start command to restart"
        return response


if __name__ == "__main__":

    print(get_user_words("akshayanagaraj00@gmail.com"))
