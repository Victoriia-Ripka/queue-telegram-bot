import mysql.connector

mydb = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="password",
    database='queue-bot-kpi',
    auth_plugin='mysql_native_password'
)