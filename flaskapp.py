from flask import Flask, request
from flask_restful import Resource, Api
from sqlalchemy import create_engine

e = create_engine('sqlite:///app-root/data/advantages.db')

app = Flask(__name__)
api = Api(app)

class HelloWorld(Resource):
    def get(self):
        conn = e.connect()
        query = conn.execute("SELECT name FROM Heroes")
        return {'Heroes': [i[0] for i in query.cursor.fetchall()]}

#         return {'hello': 'world'}

api.add_resource(HelloWorld, '/')

if __name__ == '__main__':
    app.run(debug=True)
