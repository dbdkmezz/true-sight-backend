from flask import Flask, request
from flask_restful import Resource, Api
from sqlalchemy import create_engine

e = create_engine('sqlite:///app-root/data/advantages.db')

app = Flask(__name__)
api = Api(app)

class HelloWorld(Resource):
    def get(self):
        return {'hello': 'world'}

class heroes(Resource):
    def get(self):
        conn = e.connect()
        query = conn.execute("SELECT name FROM Heroes")
        return {'Heroes': [i[0] for i in query.cursor.fetchall()]}

class hero_name(Resource):
    def get(self, hero_id):
        conn = e.connect()
        query = conn.execute("SELECT name FROM Heroes WHERE Heroes._id = {}".format(hero_id))
        return {'Name': [i[0] for i in query.cursor.fetchall()]}


api.add_resource(HelloWorld, '/')
api.add_resource(heroes, '/heroes')
api.add_resource(hero_name, '/hero/<string:hero_id>')

if __name__ == '__main__':
    app.run(debug=True)
#    app.run(debug=True)
