import mysql.connector

database = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="todo_list"
)
