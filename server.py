from flask import Flask, render_template, request, redirect, flash, session
from mysqlconnection import connectToMySQL
import re
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = ";)"


@app.route("/")
def index():
    return render_template("index.html")


EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')


@app.route('/register', methods=["POST"])
def submit():
    is_valid = True

    if len(request.form['fname']) < 1:
        is_valid = False
        flash("Please enter a first name")

    if len(request.form['lname']) < 1:
        is_valid = False
        flash("Please enter a last name")

    if not EMAIL_REGEX.match(request.form['email']):
        is_valid = False
        flash("Invalid email address!")

    if len(request.form['password']) < 1:
        is_valid = False
        flash("Please set a good password!")

    if request.form['confirm'] != request.form['password']:
        is_valid = False
        flash("Please confirm password!")

    if is_valid:
        pw_hash = bcrypt.generate_password_hash(request.form['password'])

        query = "INSERT INTO users(first_name, last_name, email, password) VALUES(%(f)s, %(l)s, %(e)s, %(p)s);"
        data = {
            'f': request.form["fname"],
            'l': request.form["lname"],
            'e': request.form["email"],
            'p': pw_hash,
        }
        mysql = connectToMySQL("wall")
        new_email_id = mysql.query_db(query, data)
        session['userid'] = new_email_id
        session['name'] = request.form["fname"]
        return redirect("/success")

    else:
        return redirect("/")


@app.route("/login", methods=["POST"])
def login():
    mysql = connectToMySQL("wall")
    query = "SELECT * FROM users WHERE email = %(e)s;"
    data = {'e': request.form['email']}
    result = mysql.query_db(query, data)
    if result:
        if bcrypt.check_password_hash(result[0]['password'], request.form['password']):
            session['userid'] = result[0]['id']
            return redirect('/success')
    flash("You failed.")
    return redirect("/")


@app.route("/success")
def success():
    print("*"*50)
    print("I'm in /success")
    if not 'userid' in session:
        return redirect('/')

    mysql = connectToMySQL("wall")
    query = "SELECT * FROM users WHERE id != %(i)s;"
    data = {'i': session['userid']}
    users = mysql.query_db(query, data)
    print(users)

    mysql = connectToMySQL("wall")
    query = "SELECT wall.messages.*, users.first_name FROM messages JOIN users ON messages.from_id = users.id WHERE messages.to_id = %(i)s;"
    #  WHERE messages.to_id = %(i)s;"
    data = {'i': session['userid']}
    messages_bd = mysql.query_db(query, data)
    print(messages_bd)

    # cn = connectToMySQL("wall")
    # query = "SELECT COUNT(*) FROM messages WHERE to_id = %(i)s;"
    # data = {'i' : session['userid']}
    # count = cn.query_db(query, data)
    # print("*"*50)
    # print(count)

    return render_template("wall.html", users=users, messages=messages_bd)


@app.route("/send", methods=["POST"])
def send():
    mysql = connectToMySQL("wall")
    query = "INSERT INTO messages (message, to_id, from_id) VALUES ( %(m)s, %(t)s, %(f)s );"
    data = {
        'm': request.form['text'],
        't': request.form['to_id'],
        'f': session['userid']
    }
    send_message = mysql.query_db(query, data)
    return redirect('/success')


@app.route("/logout")
def leave():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
