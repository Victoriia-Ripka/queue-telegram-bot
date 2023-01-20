import mysql.connector

mydb = None
my_cursor = None
password = 'password'


def connect_to_server():
    global mydb, my_cursor
    try:
        mydb = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password=password,
            auth_plugin='mysql_native_password'
        )
        my_cursor = mydb.cursor()
    except mysql.connector.Error:
        print('\033[91mConnectionError: Connection to the server failed\033[0m')
        exit(2)


def start_settings():
    if mydb and my_cursor:
        query = """SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;"""
        my_cursor.execute(query)
        mydb.commit()

        query = """SET @OLD_FOREIGN_KEY_CHECKS = @@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS = 0;"""
        my_cursor.execute(query)
        mydb.commit()

        query = """SET @OLD_SQL_MODE = @@SQL_MODE, SQL_MODE =
'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';
        """
        my_cursor.execute(query)
        mydb.commit()
    else:
        print('\033[91mQueryError: No valid connection to database for commiting a query\033[0m')
        exit(3)


def create_database(group_id):
    if mydb and my_cursor:
        query = f"""CREATE SCHEMA IF NOT EXISTS `{group_id}`
                    DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"""
        my_cursor.execute(query)
        mydb.commit()
    else:
        print('\033[91mQueryError: No valid connection to database for commiting a query\033[0m')
        exit(3)


# def use_database(group_id):
#     if mydb and my_cursor:
#         query = f"""USE `{group_id}`;"""
#         my_cursor.execute(query)
#         mydb.commit()
#     else:
#         print('\033[91mQueryError: No valid connection to database for commiting a query\033[0m')
#         exit(3)


def create_tables(group_id):
    if mydb and my_cursor:
        # таблиця "Предмети"
        query = f"""CREATE TABLE IF NOT EXISTS `{group_id}`.`Subjects`
                   (
                       `subject_id` INT          NOT NULL AUTO_INCREMENT,
                       `title`      VARCHAR(200) NOT NULL,
                       `id_teacher` INT          NOT NULL,
                       PRIMARY KEY (`subject_id`),
                       UNIQUE INDEX `title_UNIQUE` (`title` ASC) VISIBLE,
                       UNIQUE INDEX `subject_id_UNIQUE` (`subject_id` ASC) VISIBLE,
                       CONSTRAINT `fk_id_teacher`
                   	       FOREIGN KEY (`id_teacher`)
                               REFERENCES `Teachers` (`id_teacher`)
                   		       ON DELETE NO ACTION
                   		       ON UPDATE CASCADE
                   )
                   ENGINE = InnoDB;"""
        my_cursor.execute(query)
        mydb.commit()

        # таблиця "Cтуденти"
        query = f"""CREATE TABLE IF NOT EXISTS `{group_id}`.`Students`
                   (
                       `telegram_user_id` CHAR(12)     NOT NULL,
                       `username`         VARCHAR(70)  NULL,
                       `firstname`        VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
                       PRIMARY KEY (`telegram_user_id`),
                       UNIQUE INDEX `telegram_user_id_UNIQUE` (`telegram_user_id` ASC) VISIBLE,
                       UNIQUE INDEX `username_UNIQUE` (`username` ASC) VISIBLE
                   )
                   ENGINE = InnoDB;"""
        my_cursor.execute(query)
        mydb.commit()

        # таблиця "Черги"
        query = f"""CREATE TABLE IF NOT EXISTS `{group_id}`.`Queues`
                   (
                       `id_queue`   INT NOT NULL AUTO_INCREMENT,
                       `subject_id` INT NOT NULL,
                       PRIMARY KEY (`id_queue`),
                       UNIQUE INDEX `id_queue_UNIQUE` (`id_queue` ASC) VISIBLE,
                       UNIQUE INDEX `subject_id_UNIQUE` (`subject_id` ASC) VISIBLE,
                       CONSTRAINT `subject_id fk from Queue to Subjects`
                           FOREIGN KEY (`subject_id`)
                               REFERENCES `Subjects` (`subject_id`)
                               ON DELETE CASCADE
                               ON UPDATE CASCADE
                   )
                   ENGINE = InnoDB;"""
        my_cursor.execute(query)
        mydb.commit()

        # таблиця "Записи"
        query = f"""CREATE TABLE IF NOT EXISTS `{group_id}`.`Sign_ups`
                   (
                       `id_sign_up`       INT      NOT NULL AUTO_INCREMENT,
                       `id_queue`         INT      NOT NULL,
                       `telegram_user_id` CHAR(12) NOT NULL,
                       `position`         INT      NOT NULL,
                       PRIMARY KEY (`id_sign_up`),
                       CONSTRAINT `id_queue fk from Sign_ups to Queue`
                           FOREIGN KEY (`id_queue`)
                               REFERENCES `Queues` (`id_queue`)
                               ON DELETE NO ACTION
                               ON UPDATE NO ACTION,
                     CONSTRAINT `telegram_user_id fk from Sign_ups to Students`
                           FOREIGN KEY (`telegram_user_id`)
                               REFERENCES `Students` (`telegram_user_id`)
                               ON DELETE NO ACTION
                               ON UPDATE NO ACTION
                   )
                   ENGINE = InnoDB;"""
        my_cursor.execute(query)
        mydb.commit()

        # таблиця "Викладачі"
        query = f"""CREATE TABLE IF NOT EXISTS `{group_id}`.`Teachers`
                   (
                       `id_teacher`        INT          NOT NULL AUTO_INCREMENT,
                       `name`              VARCHAR(200) NOT NULL,
                       `username_telegram` VARCHAR(60)  NULL,
                       `phone_number`      VARCHAR(20)  NULL,
                       `email`             VARCHAR(70)  NULL,
                       `info`              TEXT(1000)   CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL,
                       PRIMARY KEY (`id_teacher`),
                       UNIQUE INDEX `id_teacher_UNIQUE` (`id_teacher` ASC) VISIBLE,
                       UNIQUE INDEX `name_UNIQUE` (`name` ASC) VISIBLE
                   )
                   ENGINE = InnoDB;"""
        my_cursor.execute(query)
        mydb.commit()

        # таблиця "Системні налаштування"
        query = f"""CREATE TABLE IF NOT EXISTS `{group_id}`.`System_settings`
                        (
                            `max_in_queue`    INT          NOT NULL DEFAULT 40,
                            `active_subject`  VARCHAR(200) NOT NULL DEFAULT '',
                            `active_student`  INT          NOT NULL DEFAULT 0
                        )
                        ENGINE = InnoDB;"""
        my_cursor.execute(query)
        mydb.commit()
        query = f'INSERT INTO `{group_id}`.`System_settings` () VALUES ();'
        my_cursor.execute(query)
        mydb.commit()
    else:
        print('\033[91mQueryError: No valid connection to database for commiting a query\033[0m')
        exit(3)


def end_settings():
    if mydb and my_cursor:
        query = """SET SQL_MODE=@OLD_SQL_MODE;"""
        my_cursor.execute(query)
        mydb.commit()

        query = """SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;"""
        my_cursor.execute(query)
        mydb.commit()

        query = """SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;"""
        my_cursor.execute(query)
        mydb.commit()
    else:
        print('\033[91mQueryError: No valid connection to database for commiting a query\033[0m')
        exit(3)


def delete_database(group_id):
    entered_password = input('Enter a password to drop a database:')
    if entered_password == password:
        print('\033[92mAuthorized! Access permitted!\033[0m')
        if mydb and my_cursor:
            query = f"""DROP SCHEMA IF EXISTS `{group_id}`;"""
            my_cursor.execute(query)
            mydb.commit()
            print('\n\033[92mDatabase was successfully deleted!\033[0m')
        else:
            print('\033[91mQueryError: No valid connection to database for committing a query\033[0m')
            exit(3)
    else:
        print('\033[91mThe password is wrong! Access denied!\033[0m')
