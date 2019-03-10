

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
        
