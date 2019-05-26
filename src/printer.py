import re
from collections import Counter

from src import CONSTANTS
from src import helpers


class Printer:
    def __init__(self):
        pass

    def display_emails(self, emails_list):
        template_body = "{email_id:>8} | {sender:>{size_email}} | {date:>{size_date}} | {subject:<}"
        template_head = "{email_id:>8} | {sender:^{size_email}} | {date:^{size_date}} | {subject:<}"

        emails_list = helpers.sort_emails_by_date(emails_list)

        size_email = helpers.get_max_sender_size(emails_list)
        size_date = len(self._formatize_date(emails_list[0].date))

        title = template_head.format(
            email_id="EMAIL_ID",
            sender="FROM",
            date="DATE",
            subject="SUBJECT",
            size_email=size_email,
            size_date=size_date,
        )

        print()
        print(title)
        for email_msg in emails_list:
            print(
                template_body.format(
                    email_id=email_msg.id.decode(),
                    sender=email_msg.sender,
                    subject=email_msg.subject,
                    date=self._formatize_date(email_msg.date),
                    size_email=size_email,
                    size_date=size_date,
                )
            )
        print()

    def print_one_email(self, email_msg):
        email_msg = email_msg[0]

        header = {
            "From": email_msg.sender,
            "To": email_msg.receiver,
            "Cc": email_msg.cc,
            "Bcc": email_msg.bcc,
            "Subject": email_msg.subject,
            "Date": email_msg.date,
        }

        print()
        for title, content in header.items():
            if content:
                print(title, ":", content)

        print("\n")
        print(email_msg.content.decode(errors="replace"))

    def errors(self, errors):
        template = "{count:>5} | {error:<}"

        print()
        print("=" * 100)

        print("{} errors happened\n".format(sum(errors.values())))

        print(template.format(count="Count", error="Details"))
        for error, count in errors.items():
            print(template.format(count=count, error=error))

        print("=" * 100)
        print()

    @staticmethod
    def _formatize_date(date):
        return date.strftime("%Y-%m-%d at %T")

    @staticmethod
    def input():
        out = ""

        while not out:
            out = input(">>> ")

        return out

    def print_mailboxes(self, mailboxes, current_mailbox):
        max_size_name = max(len(x[0]) for x in mailboxes.items())
        template = "{id:2} | {name:<{max_size}} | {count:<}"

        print(
            "Here is all the available mailboxes on your account\n"
            "You can select any of them using -sb ID\n\n"
            "Currently selected mailbox: {}\n".format(current_mailbox)
        )

        title = template.format(
            id="ID", name="Name", count="Total emails", max_size=max_size_name
        )

        print(title)
        for id_, (name, total_emails) in enumerate(mailboxes.items()):
            print(
                template.format(
                    id=id_,
                    name=name,
                    count=total_emails,
                    max_size=max_size_name,
                )
            )

    def choose_account(self, config):
        print("Which account would you like to log into ?\n")

        choices = []
        for email_address in config:
            if email_address != "DEFAULT":
                print("{} - {}".format(len(choices) + 1, email_address))
                choices.append(email_address)

        print()
        answer = input()

        while True:
            if answer in choices:
                return config[answer]

            if answer.isdigit() and 0 < int(answer) <= len(choices):
                return config[choices[int(answer) - 1]]

            answer = input(
                "\nSorry, I haven't understood your choice.\n"
                "Please try again:\n"
            )

        return answer

    def ask_for_delete_mailbox(self, mailboxes):
        print("Select the mailbox where deleted emails should be stored:")

        choices = []
        for mailbox in mailboxes:
            print("{} - {}".format(len(choices) + 1, mailbox))
            choices.append(mailbox)

        print()
        answer = input()

        while True:
            if answer in choices:
                return answer

            if answer.isdigit() and 0 < int(answer) <= len(choices):
                return choices[int(answer) - 1]

            answer = input(
                "\nSorry, I haven't understood your choice.\n"
                "Please try again:\n"
            )

    def _get_email_content(self, email_msg):
        email_msg = email_msg[0]
        type_ = email_msg.get_content_maintype()

        if type_ == "text":
            return email_msg.get_payload(decode=True)
        elif "image" in type_:
            return b" [IMAGE] "
        elif "multipart" in type_:
            content = b""
            for part in email_msg.get_payload():
                content += self._get_email_content(part)
            return content
        else:
            return b""

    def summary_by_top_senders(self, data, top=10):
        data = self.group_email_by_sender(data)

        formatter = "{count:>5} | {sender:{size_email}}"

        size_email = len(max(data, key=len))

        titles = formatter.format(
            sender="From", count="Count", size_email=size_email
        )

        top_senders = data.most_common(top)

        print()
        print(titles)
        for sender, total in top_senders:
            print(
                formatter.format(
                    sender=sender, count=total, size_email=size_email
                )
            )
        print()

        return top_senders

    @staticmethod
    def group_email_by_sender(data):
        return Counter(msg.sender for msg in data)

    def main_menu(self):
        answer = None

        print()
        answer = self.input()

        return answer

    def ask_for_email(self, question):
        answer = ""
        pattern = "^[\w\d\-_\.]+[a-zA-Z]@[a-zA-Z][a-zA-Z\.\-]+\.[a-zA-Z]{2,}$"

        while not re.match(pattern, answer):
            if answer:
                print("This is not a valid email address\n")
            print()
            print(question)
            answer = self.input()
            print()

        return answer
