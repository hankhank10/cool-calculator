from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy

# Create our flask app
app = Flask(__name__)

# Create the database connections. I have used sqlite for simplicity but you can also use a mysql or postgres address
# SQLAlchemy only allows connection to one "default" database
# Our default is going to be the "output" database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///output_database.sqlite'

# We can connect to other databases (in this case the "input" database) by creating "binds"
app.config['SQLALCHEMY_BINDS'] = {'input_database': 'sqlite:///input_database.sqlite'}
# Full docs on multiple connections here: https://flask-sqlalchemy.palletsprojects.com/en/2.x/binds/

# This next line isn't strictly necessary but if you don't include it then sometimes flask will complain and be verbose
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Here we create the database object, which is slightly confusing as it's not a single database in this situation - it's a connection to both our databases
db = SQLAlchemy(app)
db.init_app(app)


# Define our models - this ensure that SQLAlchemy knows how to interface with them
# Note that defining them here doesn't actually create them anywhere

class InputPerson(db.Model):
    __bind_key__ = 'input_database'  # We need this here to make clear that this is in our input database
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    nickname = db.Column(db.String(50))
    gender = db.Column(db.String(6))
    age = db.Column(db.Integer)


class OutputPerson(db.Model):
    # Note we don't need to specify the bind here as it's a table in the default database
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    nickname = db.Column(db.String(50))
    gender = db.Column(db.String(6))
    age = db.Column(db.Integer)
    is_cool = db.Column(db.Boolean)

    # This is a cool way of performing functions on data without actually having it saved to the database - it is calculated each time it's called
    @property
    def first_name(self):
        return str.split(self.name)[0]


# This route creates the input database - it's included here just so you know how it works
# but you wouldn't actually need to do this in your workflow as your database already exists
@app.route('/create_input_database')
def create_input_database():

    # This deletes the existing records from the database...
    db.drop_all(bind='input_database')

    # ... and this creates the database structure
    db.create_all(bind='input_database')

    # We can now reference the InputPerson model above directly...
    new_person = InputPerson(
        name="Richard Cunningham",
        nickname="Richie",
        gender="male",
        age=19
    )

    # ...and then add that object to the database
    # Note that we don't need to say *which* database to add it to - since alchemy knows this from the model definition above
    db.session.add(new_person)

    new_person = InputPerson(
        name="Arthur Herbert Fonzarelli",
        nickname="Fonzie",
        gender="male",
        age=20
    )
    db.session.add(new_person)

    # If you want to streamline your code you can also do this, without saving to a var first
    db.session.add(InputPerson(
        name="Joanie Cunningham",
        nickname="Joanie",
        gender="female",
        age=20
    ))
    db.session.add(new_person)

    # Write everything to the database
    # If you don't do this nothing will happen
    db.session.commit()

    return "ok"


@app.route('/show_input_database')
def show_input_database():

    # Get all the records from the table
    list_of_people = InputPerson.query.all()

    # Other things you could do would be:
    # list_of_male_people = InputPerson.query.filter_by(gender="male).all()
    # how_many_male_people = InputPerson.query.filter_by(gender="male").count()
    # list_of_old_people = InputPerson.query.filter(InputPerson.age > 50).all()
    # list_of_old_male_people = InputPerson.query.filter(InputPerson.age > 50, InputPerson.gender == "male")

    # Note that filter_by() and filter() are different functions
    # In short filter_by() is simpler but only allows you to do = comparisons
    # filter() allows you to do standard python comparisons such as ==, >, < etc
    # In filter_by you don't need to specify the table name, in filter you do

    # We want to output a list of dictionaries via json, which means we need an empty list to start with
    output_list = []

    # Iterate through each result from the DB query, put the data from the query into a dictionary and then append that
    # dictionary to the output list
    for person in list_of_people:
        output_person = {
            'id': person.id,
            'name': person.name,
            'nickname': person.nickname,
            'gender': person.gender,
            'age': person.age,
        }
        output_list.append(output_person)

    # Return the output list in easy to read JSON
    return jsonify(output_list)


@app.route('/show_output_database')
def show_output_database():

    try:
        list_of_people = OutputPerson.query.all()
    except:
        return jsonify (
            {'status': 'error',
             'what_happened': 'Could not access output database. Did you create it already?'}
        )

    # We want to output a list of dictionaries via json, which means we need an empty list to start with
    output_list = []

    # Iterate through each result from the DB query, put the data from the query into a dictionary and then append that dictionary to the output list
    for person in list_of_people:
        output_person = {
            'id': person.id,
            'name': person.name,
            'nickname': person.nickname,
            'gender': person.gender,
            'age': person.age,
            'is_cool': person.is_cool,
            'first_name': person.first_name  #Note that this hasn't actually been stored, it's just generated automatically by the @property decorator in the class
        }
        output_list.append(output_person)

    # Return the output list in easy to read JSON
    return jsonify(output_list)


@app.route('/process_everything')
def process_everything():

    # We want to clear everything in our output database and then recreate it
    # By specifying bind=None here we make clear that it should be the default database which is dropped and created
    # If you were to just specify drop_all() and create_all() this would wipe all databases
    db.drop_all(bind=None)
    db.create_all(bind=None)

    # Query the input database to get all people and put it into a list
    list_of_input_people = InputPerson.query.all()

    number_of_people_processed = 0
    number_of_cool_people_processed = 0
    for input_person in list_of_input_people:

        # Do the processing
        if input_person.nickname == "Fonzie":
            is_this_person_cool = True
            number_of_cool_people_processed = number_of_cool_people_processed + 1
        else:
            is_this_person_cool = False

        # Create the new record
        new_output_person = OutputPerson (
            name=input_person.name,
            nickname=input_person.nickname,
            gender=input_person.gender,
            age=input_person.age,
            is_cool=is_this_person_cool
        )

        # Write the record in the output database
        db.session.add(new_output_person)

        number_of_people_processed = number_of_people_processed + 1

    db.session.commit()

    return (str(number_of_people_processed) + " people processed of which " + str(number_of_cool_people_processed) + " were cool")


@app.route('/create_lots_of_people')
def create_lots_of_people():
    for a in range(1,100000):
        db.session.add(InputPerson(
          name="Someone else",
          nickname="Too boring to have a nickname",
          gender="Unclear",
          age=25
        ))

    db.session.commit()
    return "100,000 people created in input database"


# Index route
@app.route('/')
def index_route():
    return render_template('howto.html')

# Main loop
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=12345, debug=True)
