import psycopg2

class Database:
    def __init__(self) -> None:
        self._conn = psycopg2.connect()
        self._conn.info.status

    def add_to_inbox(self, task_title: str):
        with self._conn.cursor() as curs:
            # curs.execute("INSERT INTO entity VALUES (id, )")