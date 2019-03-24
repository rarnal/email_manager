from src import helpers
from src import app


def main():

    config = helpers.get_config()
    application = app.Motor(config)
    application.run()




if __name__ == '__main__':
    main()
