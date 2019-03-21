import re

import CONSTANTS


class Printer:
    def __init__(self):
        pass

    @staticmethod
    def table_summary(data):
        formatter = "{id:>5} | {count:>5} | {sender:40}"
        titles = formatter.format(id='id',
                                  sender='From',
                                  count='count')
        print()
        print(titles)
        for i, (sender, total) in enumerate(data.most_common(10), 1):
            print(formatter.format(id=i,
                                   sender=sender,
                                   count=total))
        print()

    @staticmethod
    def main_menu(question, answers):
        answer = None
        print()

        while answer not in answers:
            if answer:
                print("Incorrect input.\n"
                      "Please give me the number of the chosen action\n")
            print(question)
            for id_ in answers:
                print("({}) - {}"
                      .format(id_, CONSTANTS.DESCRIPTION_ACTIONS[id_]))
            print()
            answer = input()
            if answer.isdigit():
                answer = int(answer)

        return answer

    @staticmethod
    def ask_for_email(question):
        answer = ''
        pattern = "^[\w\d\-_\.]+[a-zA-Z]@[a-zA-Z][a-zA-Z\.\-]+\.[a-zA-Z]{2,}$"
        
        while not re.match(pattern, answer):
            if answer:
                print("This is not a valid email address\n")
            print()
            print(question)
            answer = input()
            print()

        return answer
            








        
