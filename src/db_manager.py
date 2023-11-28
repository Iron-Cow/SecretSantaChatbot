import sqlite3


class DbDriver(object):
    def __init__(self):
        # Connect to the SQLite database. If the file does not exist, it will be created.
        self._conn = sqlite3.connect('secret_santa_db.sqlite')
        self._cursor = self._conn.cursor()
        self.config_db()

    def config_db(self):
        # Define the SQL query for creating a new table. Note that SQLite uses AUTOINCREMENT keyword.
        queries = [
            """
            CREATE TABLE IF NOT EXISTS rooms 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_tg_id INTEGER);
            """,
            """
            CREATE TABLE IF NOT EXISTS players 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR, tg_id INTEGER, pair BOOLEAN, 
            room_id INTEGER, FOREIGN KEY (id) REFERENCES rooms(id) ON DELETE CASCADE);
            """
        ]

        for query in queries:
            self.execute_dml(query=query, params=())

    def execute_dml(self, query: str, params: tuple) -> None:
        # Execute a DML (Data Manipulation Language) command
        self._cursor.execute(query, params)
        self._conn.commit()

    def execute_select(self, query: str, params: tuple) -> list:
        # Execute a SELECT query and return the results
        self._cursor.execute(query, params)
        return self._cursor.fetchall()

    def close(self):
        # Close the database connection
        self._conn.close()

    def get_room_by_id(self, room_id: int):
        query = "SELECT * FROM rooms WHERE room_id = ?"
        params = (room_id,)
        self._cursor.execute(query, params)
        return self._cursor.fetchone()

    def get_all_rooms(self):
        query = "SELECT * FROM rooms"
        self._cursor.execute(query)
        return self._cursor.fetchall()

    def insert_room(self,  owner_tg_id: str):
        query = "INSERT INTO rooms (owner_tg_id) VALUES (?)"
        params = (owner_tg_id,)
        self._cursor.execute(query, params)
        self._conn.commit()
        return self._cursor.lastrowid  # Returns the ID of the newly inserted row

    def add_player(self,  name: str, tg_id: int, pair: bool, room_id: int):
        query = "INSERT INTO players (name, tg_id, pair, room_id) VALUES (?, ?, ?, ?)"
        params = (name, tg_id, pair, room_id)
        self._cursor.execute(query, params)
        self._conn.commit()
        return self._cursor.lastrowid  # Returns the ID of the newly inserted row

    def leave_room(self, tg_id: int, room_id: int):
        query = "DELETE FROM players WHERE room_id=? AND tg_id=?"
        params = (room_id, tg_id)
        self._cursor.execute(query, params)
        self._conn.commit()
        return self._cursor.lastrowid  # Returns the ID of the newly inserted row


    def get_my_rooms(self, tg_id: int):
        query = """
        SELECT rooms.id, rooms.owner_tg_id
        FROM rooms
                 LEFT JOIN main.players p ON rooms.id = p.room_id
        WHERE owner_tg_id = ?
           OR tg_id = ?
        """
        params = (tg_id,tg_id)
        self._cursor.execute(query, params)
        return self._cursor.fetchall()


    def get_room_players(self, room_id: int):
        query = """
            SELECT name, pair, tg_id FROM players WHERE room_id = ?
        """
        params = (room_id,)
        self._cursor.execute(query, params)
        return self._cursor.fetchall()
