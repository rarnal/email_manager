import re
from collections import Counter

from src import CONSTANTS


class Printer:
    def __init__(self):
        pass


    def display_emails(self, emails_list):
        template = "{id_:>8} | {sender:>30} | {date:>25} | {subject:<}"
        title = template.format(id_="id",
                                sender="From",
                                date="Date",
                                subject="Subject")
        print(title)

        for email_msg in emails_list:
            print(template.format(
                id_=email_msg['id'],
                sender=email_msg['From'],
                subject=email_msg['Subject'],
                date=self._formatize_date(email_msg['Date'])
            ))


    def _print_one_email(self, email_msg):
        template = "From: {sender}\nSubject: {subject}\n" \
                   "Date: {date}\n\n{content}\n\n"

        content = self._get_email_content(email_msg)
        content = content.decode(errors='replace')

        print(template.format(sender=email_msg['From'],
                              subject=email_msg['Subject'],
                              date=self._formatize_date(email_msg['Date']),
                              content=content))


    @staticmethod
    def _formatize_date(date):
        return date.strftime("%Y-%m-%d at %T")


    def _get_email_content(self, email_msg):
        type_ = email_msg.get_content_maintype()

        if type_ == 'text':
            return email_msg.get_payload(decode=True)
        elif 'image' in type_:
            return b" *** IMAGE *** "
        elif 'multipart' in type_:
            content = b''
            for part in email_msg.get_payload():
                content += self._get_email_content(part)
            return content
        else:
            return b''


    def summary_by_top_senders(self, data, top=10):
        data = self.group_email_by(data, 'From')

        formatter = "{id:>5} | {count:>5} | {sender:40}"
        titles = formatter.format(id='id',
                                  sender='From',
                                  count='count')

        top_senders = data.most_common(top)
        ids = []

        print()
        print(titles)
        for i, (sender, total) in enumerate(top_senders, 1):
            ids.append(i)
            print(formatter.format(id=i,
                                   sender=sender,
                                   count=total))
        print()

        return ids, top_senders


    @staticmethod
    def group_email_by(data, by):
        return Counter(msg[by] for msg in data)


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










