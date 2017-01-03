from flask import Flask, render_template

app = Flask(__name__)
app.config.update(
        DEBUG = True
    )


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/showUsers')
def show_users():
    return render_template('listAllUsers.html')


if __name__ == '__main__':
    app.run()
