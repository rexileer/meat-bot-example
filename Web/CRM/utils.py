from data.constants import translit_letter


def translit_letters(word):
    new_string = ""
    for letter in word.replace("-", "_").replace(" ", "_"):
        if letter.lower() in translit_letter.keys():
            new_string += translit_letter.get(letter.lower())
        else:
            new_string += letter.lower()
    return new_string.replace("'", "").replace('"', "").replace(" ", "")
