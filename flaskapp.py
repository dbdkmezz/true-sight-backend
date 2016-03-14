from flask import Flask, request
from flask_restful import Resource, Api, fields, marshal_with
import sqlite3

TABLE_FILE_NAME = "app-root/data/advantages.db"

app = Flask(__name__)
api = Api(app)

resource_fields = {
    'id_num': fields.Integer,
    'name': fields.String,
    'is_carry': fields.Boolean,
    'is_support': fields.Boolean,
    'is_mid': fields.Boolean,
    'is_off_lane': fields.Boolean,
    'is_jungler': fields.Boolean,
    'is_roaming': fields.Boolean,
    'advantages': fields.List(fields.Float),
}

class AdvantageDataForAHero:
    def __init__(self, id_num, name, is_carry, is_support, is_mid, is_off_lane, is_jungler, is_roaming):
        self.id_num = id_num
        self.name = name
        self.is_carry = is_carry
        self.is_support = is_support
        self.is_mid = is_mid
        self.is_off_lane = is_off_lane
        self.is_jungler = is_jungler
        self.is_roaming = is_roaming
        self.advantages = []

class HelloWorld(Resource):
    def get(self):
        return {'hello': 'world'}

class heroes(Resource):
    def get(self):
        conn = sqlite3.connect(TABLE_FILE_NAME)
        c = conn.cursor()
        query = c.execute("SELECT name FROM Heroes")
        return {'Heroes': [i[0] for i in query.fetchall()]}

class hero_name(Resource):
    def get(self, hero_id):
        conn = sqlite3.connect(TABLE_FILE_NAME)
        c = conn.cursor()
        query = c.execute("SELECT name FROM Heroes WHERE Heroes._id = {}".format(hero_id))
        return {'Name': [i[0] for i in query.fetchall()]}

class Advantages(Resource):
    @marshal_with(resource_fields, envelope='data')
    def get(self, name1, name2, name3, name4, name5):
        conn = sqlite3.connect(TABLE_FILE_NAME)
        c = conn.cursor()

        c.execute("SELECT _id, name, is_carry, is_support, is_mid, is_off_lane, is_jungler, is_roaming FROM Heroes")
        heroes = []
        for row in c.fetchall():
            heroes.append(AdvantageDataForAHero(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]))

        enemyNames = [name1, name2, name3, name4, name5]
        for hero in heroes:
            for enemyName in enemyNames:
                Advantages.add_advantage(c, hero, enemyName)
                
        return heroes

    @staticmethod
    def add_advantage(c, hero, enemyName):
        c.execute("""SELECT advantage
             FROM Heroes, Advantages
             WHERE Heroes.name = \'{}\'
             AND Heroes._id = Advantages.enemy_id
             AND Advantages.hero_id = {}""".format(enemyName, hero.id_num))
        result = c.fetchone()
        if(result == None):
            hero.advantages.append(None)
        else:
            hero.advantages.append(result[0])


# class advantages(Resource):
#     def get(self, name1, name2, name3, name4, name5):
#         conn = sqlite3.connect(TABLE_FILE_NAME)
#         c = conn.cursor()
#         c.execute("SELECT name FROM Heroes")
# #         c.execute("SELECT _id, name, is_carry, is_support, is_mid, is_off_lane, is_jungler, is_roaming FROM Heroes")
#         heroes = []
#         for row in c.fetchall():
#             heroes.append(c)

#         return {'heroes' : [i for i in heroes]}



api.add_resource(HelloWorld, '/')
api.add_resource(heroes, '/heroes')
api.add_resource(hero_name, '/hero/<string:hero_id>')
api.add_resource(Advantages, '/advantages/<string:name1>/<string:name2>/<string:name3>/<string:name4>/<string:name5>')

if __name__ == '__main__':
    app.run(debug=True)
#    app.run(debug=True)



# from flask import Flask, request
# from flask_restful import Resource, Api
# from sqlalchemy import create_engine

# e = create_engine('sqlite:///app-root/data/advantages.db')

# app = Flask(__name__)
# api = Api(app)

# class AdvantageDataForAHero:
#     id_num = None
#     name = None
#     is_carry = None
#     is_support = None
#     is_mid = None
#     is_off_lane = None
#     is_jungler = None
#     is_roaming = None

#     def __init__(self, id_num, name, is_carry, is_support, is_mid, is_off_lane, is_jungler, is_roaming):
#         self.id_num = id_num
#         self.is_carry = is_carry
#         self.is_support = is_support
#         self.is_mid = is_mid
#         self.is_off_lane = is_off_lane
#         self.is_jungler = is_jungler
#         self.is_roaming = is_roaming

# class HelloWorld(Resource):
#     def get(self):
#         return {'hello': 'world'}

# class heroes(Resource):
#     def get(self):
#         conn = e.connect()
#         query = conn.execute("SELECT name FROM Heroes")
#         return {'Heroes': [i[0] for i in query.cursor.fetchall()]}

# class hero_name(Resource):
#     def get(self, hero_id):
#         conn = e.connect()
#         query = conn.execute("SELECT name FROM Heroes WHERE Heroes._id = {}".format(hero_id))
#         return {'Name': [i[0] for i in query.cursor.fetchall()]}

# class advantages(Resource):
#     def get(self, name1, name2, name3, name4, name5):
#         conn = e.connect()
#         query = conn.execute("SELECT * FROM Heroes")
#         heroes = []
#         for hero in query.cursor.fetchall():
#             heroes.append(hero)
#         return {'heroes' : [i[0] for i in heroes]}


# api.add_resource(HelloWorld, '/')
# api.add_resource(heroes, '/heroes')
# api.add_resource(hero_name, '/hero/<string:hero_id>')
# api.add_resource(advantages, '/advantages/<string:name1>/<string:name2>/<string:name3>/<string:name4>/<string:name5>')

# if __name__ == '__main__':
#     app.run(debug=True)
# #    app.run(debug=True)
