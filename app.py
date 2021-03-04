from dataclasses import dataclass

from flask import Flask, json, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask import request


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:rootroot@localhost/crm'
db = SQLAlchemy(app)

@dataclass
class User(db.Model):
    id: int
    age: int
    name: str
    id = db.Column(db.Integer, primary_key=True)
    age = db.Column(db.Integer, nullable=True)
    name = db.Column(db.String(63), nullable=True)
    test = db.Column(db.Integer, nullable=True)

    def get_model_class(self):
        return self.model_class

    @classmethod
    def custom_filter(model_class, filter_condition):
        '''
        Return filtered queryset based on condition.
        :param query: takes query
        :param filter_condition: Its a list, ie: [(key,operator,value)]
        operator list:
            eq for ==
            lt for <
            ge for >=
            in for in_
            like for like
            value could be list or a string
        :return: queryset
        '''
        __query = db.session.query(model_class)
        for raw in filter_condition:
            try:
                key, op, value = raw
            except ValueError:
                raise Exception('Invalid filter: %s' % raw)
            column = getattr(model_class, key, None)
            if not column:
                raise Exception('Invalid filter column: %s' % key)
            if op == 'in':
                if isinstance(value, list):
                    filt = column.in_(value)
                else:
                    filt = column.in_(value.split(','))
            else:
                try:
                    attr = list(filter(lambda e: hasattr(column, e % op), ['%s', '%s_', '__%s__']))[0] % op
                except IndexError:
                    raise Exception('Invalid filter operator: %s' % op)
                if value == 'null':
                    value = None
                filt = getattr(column, attr)(value)
            __query = __query.filter(filt)
        return __query


db.create_all()


@app.route('/user', methods=['GET'])
def get_users():
    filtered = create_filter_object(request.args)

    res = User.custom_filter(filtered).all()
    # res = User.query.filter(getattr(User, 'age') > '10').all()
    # attr = getattr(User, 'age')
    # print(getattr(User, 'age')('10'))
    # res = User.custom_filter([('age', 'ge', '10'), ('test', 'ge', '20')]).all()
    # res = User.query.filter_by(User.age >= 10)
    return jsonify(res)


@app.route('/user', methods=['POST'])
def create_user():
    data = json.loads(request.data)
    user = User(age=data["age"], name=data["name"], test=data["test"])
    db.session.add(user)
    db.session.commit()
    print(data)
    return data


def create_filter_object(arguments):
    filter = {}
    for args in arguments:
        filter[args] = {}
        r = arguments.getlist(args)
        for filterArg in r:
            row = filterArg.split(':')
            filter[args][row[0]] = row[1]

    arrToFilter = []
    for key, value in filter.items():
        for keyInside, valueInside in value.items():
            tplItem = (key, keyInside, valueInside)
            arrToFilter.append(tplItem)

    return arrToFilter


if __name__ == '__main__':
    app.run()
