

class Printer:
    def __init__(self):
        pass

    def table_summary(self, data):
        formatter = "{id:5d} | {sender:30} | {count:5} | {size:8}"
        titles = formatter.format(id='id',
                                  sender='sender',
                                  count='count',
                                  size='size')

        print(titles)
        for row in data:
            print(formatter.format(id=row['id'],
                                   sender=row['sender'],
                                   count=row['count'],
                                   size=row['size']))
        
