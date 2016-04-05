import sqlite3
import os

import scraper

TABLE_FILE_NAME = "advantages.db"

class DatabaseWriter:

    c = None
    conn = None
    ignore_errors = False

    def __init__(self, results, ignore_errors):
        self.ignore_errors = ignore_errors
        self.create_table()
        self.add_hero_names(results)
        self.add_advantages(results)
        self.save_table()

    def create_table(self):
        # ensure we delete the existing file, if it exists
        if(os.path.isfile(TABLE_FILE_NAME)):
            os.remove(TABLE_FILE_NAME)

        self.conn = sqlite3.connect(TABLE_FILE_NAME)
        self.c = self.conn.cursor()
        
        self.c.execute("""CREATE TABLE Heroes (
                         _id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, 
                         name TEXT,
                         is_carry BOOLEAN,
                         is_support BOOLEAN,
                         is_off_lane BOOLEAN,
                         is_jungler BOOLEAN,
                         is_mid BOOLEAN,
                         is_roaming BOOLEAN)""")
        self.c.execute("""CREATE TABLE Advantages (
                         hero_id INTEGER,
                         enemy_id INTEGER,
                         advantage DECIMAL(2,2))""")

    def add_hero_names(self, results):
        for hero in results:
            self.c.execute("INSERT INTO Heroes (name, is_carry, is_support, is_off_lane, is_jungler, is_mid, is_roaming) VALUES ('{}', {}, {}, {}, {}, {}, {})".format(hero.database_name, hero.is_carry, hero.is_support, hero.is_off_lane, hero.is_jungler, hero.is_mid, hero.is_roaming))

    def add_advantages(self, results):
        for hero in results:
            hero_id = self.get_hero_id(hero)
            for enemy in hero.advantages_data:
                enemy_id = self.get_hero_id(enemy)
                self.c.execute("INSERT INTO Advantages (hero_id, enemy_id, advantage) VALUES ({}, {}, {})".format(hero_id, enemy_id, enemy.advantage))


    def save_table(self):
        self.conn.commit()
        self.conn.close()
        print("\nDatabase written sucessfully to {}.".format(TABLE_FILE_NAME))

    def get_hero_id(self, hero):
        self.c.execute("SELECT _id FROM Heroes WHERE name='{}';".format(hero.database_name))
        fetch_result = self.c.fetchone()
        if(self.ignore_errors == True and fetch_result == None):
            return -1
        else:
            return fetch_result[0]


