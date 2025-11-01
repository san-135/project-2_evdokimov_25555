import prompt


def welcome():
    print('Первая попытка запустить проект!')
    print('\n *** ')
    help()
    while True:
        user_command = prompt.string('Введите команду: ').strip().lower()
        match user_command:
            case 'help':
                help()
            case 'exit' | 'quit' | 'q':
                break
    

def help():
    print('<command> exit - выйти из программы \n'
    '<command> help - справочная информация \n')
        