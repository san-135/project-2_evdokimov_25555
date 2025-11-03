


# def welcome():
#     print('Первая попытка запустить проект!')
#     print('\n *** ')
#     help()
#     while True:
#         user_command = prompt.string('Введите команду: ').strip().lower()
#         match user_command:
#             case 'help':
#                 help()
#             case 'exit' | 'quit' | 'q':
#                 break
    

# def help():
#     print('<command> exit - выйти из программы \n'
#     '<command> help - справочная информация \n')


import prompt
from src.primitive_db.core import create_table, drop_table, help, list_tables
from src.primitive_db.utils import load_metadata, save_metadata


META_PATH = "db_meta.json"


# def parse_columns(parts: list) -> list:
#     # оставляет как есть для простоты: части после команды — столбцы
#     return parts


def run():
    metadata = load_metadata(META_PATH)

    print("База данных запущена. Введите команду. help для справки.")
    while True:
        try:
            user_input = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue

        tokens = user_input.split()
        cmd = tokens[0].lower()

        match cmd:
            case "create_table":
                if len(tokens) < 3:
                    print("Некорректная команда - ожидались имя таблицы и столбцы.")
                    continue
                table_name = tokens[1]
                columns = tokens[2:]
                try:
                    metadata = create_table(metadata, table_name, columns)
                    save_metadata(META_PATH, metadata)
                except ValueError as ve:
                    print(f"Ошибка: {ve}")

            case "drop_table":
                if len(tokens) != 2:
                    print("Некорректная команда - ожидалось имя таблицы.")
                    continue
                table_name = tokens[1]
                metadata = drop_table(metadata, table_name)
                save_metadata(META_PATH, metadata)

            case "list_tables":
                tabs = list_tables(metadata)
                print(" tables: " + (", ".join(tabs) if tabs else ""))
            case "help":
                help()
            case "exit" | "^[": # "exit" или кнопка Esc
                break
            case _:
                print(f"Некорректная команда: {cmd}. Попробуйте снова.")

    print("Выход из программы.")

