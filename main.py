import helpers
import motor


def main():

    config = helpers.get_config()
    app = motor.Motor(config)




if __name__ == '__main__':
    main()
