import mysql.connector
from mysql.connector import Error

def runQuerytest():
    try:
     mydb = mysql.connector.connect(
     host="localhost",
     user="root",
     password="",
     database="school_db"
     )

     mycursor = mydb.cursor()

     mycursor.execute("SELECT * FROM students")

     results = mycursor.fetchall()
     for row in results:
         print(row)

     mycursor.close()
     mydb.close()

    except Error as e:
          print(f"Database error encountered -> {e}")

if __name__ == "__main__":
    runQuerytest()