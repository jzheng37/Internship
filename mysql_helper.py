import mysql.connector
from mysql.connector import Error


class MySQLHelper:
    def __init__(self, host="localhost", user="root", password="", database="school_db"):
        self.config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database
        }

    def _get_connection(self):
        return mysql.connector.connect(**self.config)

    def execute_modify(self, sql, params=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params or ())
            conn.commit()
            return cursor.rowcount
        except Error as e:
            print(f"[Database Error]: {e}")
            conn.rollback()
            return 0
        finally:
            cursor.close()
            conn.close()

    def execute_modify_many(self, sql, params_list):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.executemany(sql, params_list)
            conn.commit()
            return cursor.rowcount
        except Error as e:
            print(f"[Database Error]: {e}")
            conn.rollback()
            return 0
        finally:
            cursor.close()
            conn.close()

    def execute_query(self, sql, params=None):
        conn = self._get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(sql, params or ())
            return cursor.fetchall()
        except Error as e:
            print(f"[Database Error]: {e}")
            return []
        finally:
            cursor.close()
            conn.close()

if __name__ == '__main__':
    db = MySQLHelper(database="school_db")

    try:
        db.execute_modify(
            "CREATE TABLE IF NOT EXISTS students (id INT PRIMARY KEY, name VARCHAR(50), height DECIMAL(5,2));")
        db.execute_modify("TRUNCATE TABLE students;")

        insert_ok = db.execute_modify("INSERT INTO students (id, name, height) VALUES (%s, %s, %s);",
                                      (1, "Bruce", 182.5))
        select_ok = db.execute_query("SELECT * FROM students;")
        update_ok = db.execute_modify("UPDATE students SET height = %s WHERE id = %s;", (185.0, 1))
        delete_ok = db.execute_modify("DELETE FROM students WHERE id = %s;", (1,))

        if insert_ok and select_ok and update_ok and delete_ok:
            print("SUCCESS: All operations completed and verified.")
        else:
            print("Failed: One or more database operations did not return the expected result.")

    except Exception as e:
        print("Connection error -> {e}")