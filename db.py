import mysql.connector

mydb = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="iamfp_MYSQL1",
    database='queue-bot',
    auth_plugin='mysql_native_password'
)