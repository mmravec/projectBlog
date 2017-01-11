from flask import Flask, render_template, session, request, flash, url_for, redirect, render_template, abort, g
from flask_login import login_user, login_required, current_user, logout_user
from flask_login import LoginManager
from sqlalchemy import desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message, Mail
from model_db import *
from functools import wraps
from werkzeug.utils import secure_filename
import os
from prediction import NB

engine = create_engine('mysql+mysqlconnector://root:@localhost/blog', echo=True)
UPLOAD_DIR = os.path.dirname(os.path.realpath(__file__)) + '/static/postPictures'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config.update(
    DEBUG=True,
    SECRET_KEY='7d441f27d441f27567d441f2b6176a',
    SECURITY_PASSWORD_SALT='my_precious_two',

    # upload settings
    UPLOAD_FOLDER=UPLOAD_DIR,
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,

    # mail settings
    MAIL_SERVER='smtp.googlemail.com',
    MAIL_PORT=465,
    MAIL_USE_TLS=False,
    MAIL_USE_SSL=True,

    # mail accounts
    MAIL_USERNAME='martinmravec4@gmail.com',
    MAIL_PASSWORD='asdfghjkl123qwert'
)

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = 'login'

mail = Mail(app)


if not os.path.isdir(UPLOAD_DIR):
    os.mkdir(UPLOAD_DIR)
    os.chmod(UPLOAD_DIR, 777)


def allowed_file(filename):
    """Does filename have the right extension?"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    user = User(request.form['username'], request.form['password'], request.form['email'], confirmed=False)
    Session = sessionmaker(bind=engine)
    s = Session()
    s.add(user)
    s.commit()

    token = generate_confirmation_token(user.email)
    confirm_url = url_for('confirm_email', token=token, _external=True)
    html = render_template('activate.html', confirm_url=confirm_url)
    subject = "Please confirm your email."
    try:
        send_email(user.email, subject, html)
        login_user(user)

        flash('User successfully registred. A confirmation email has been sent via email.', 'success')
        return redirect(url_for('login'))
    except:
        login_user(user)
    return render_template('register.html')




@app.route('/confirm/<token>')
@login_required
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        flash('This confirmation link is invalid or has expired.', 'danger')
    Session = sessionmaker(bind=engine)
    s = Session()
    user = s.query(User).filter_by(email=email).first()
    if user.confirmed:
        flash('Account allredy confirmed. Please login.', 'success')
    else:
        user.confirmed = True
        user.confirmed_on = datetime.utcnow()
        s.add(user)
        s.commit()
        flash('You have confirmed your account. Thanks!', 'success')
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    username = request.form['username']
    password = request.form['password']

    remember_me = False
    if 'remember_me' in request.form:
        remember_me = True

    Session = sessionmaker(bind=engine)
    s = Session()
    registered_user = s.query(User).filter_by(username=username).first()
    confirmed_user = s.query(User).filter_by(confirmed=True).first()
    if confirmed_user is None:
        flash('Your account has not been activated yet.', 'error')
        return redirect(url_for('login'))
    if registered_user is None:
        flash('Username or Password is invalid', 'error')
        return redirect(url_for('login'))
    if not registered_user.check_password(password):
        flash('Password is invalid', 'error')
        return redirect(url_for('login'))
    login_user(registered_user, remember=remember_me)
    flash('Logged in successfully')
    return redirect(request.args.get('next') or url_for('index', user=registered_user))


@app.route('/showUsers')
def show_users():
    return render_template('listAllUsers.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@login_manager.user_loader
def load_user(id):
    Session = sessionmaker(bind=engine)
    s = Session()
    return s.query(User).get(int(id))


@app.before_request
def before_request():
    g.user = current_user
    if current_user is None:
        return render_template('login.html')


def check_confirmed(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.confirmed is False:
            flash('Please confirm your account!', 'warning')
            return redirect(url_for('unconfirmed'))
        return func(*args, **kwargs)

    return decorated_function


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])


def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except:
        return False
    return email


def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=app.config['MAIL_USERNAME']
    )
    mail.send(msg)


@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
@login_required
@check_confirmed
def index():
    Session = sessionmaker(bind=engine)
    s = Session()
    post = s.query(Post).order_by(desc(Post.id))
    user = s.query(User).from_self().join(User.posts)

    return render_template('index.html',  user=user, post=post)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
@check_confirmed
def profile():
    return render_template('profile.html')


@app.route('/post/')
@app.route('/post/<int:id>', methods=['GET', 'POST'])
@login_required
@check_confirmed
def post(id):
    Session = sessionmaker(bind=engine)
    s = Session()
    post = s.query(Post).filter(Post.id == id)
    user = s.query(User).from_self().join(User.posts)


    if request.method == 'POST':

        predictionN = NB.make_class_prediction(request.form['comment'], NB.negative_counts, NB.prob_negative, NB.negative_review_count)
        predictionP = NB.make_class_prediction(request.form['comment'], NB.positive_counts, NB.prob_positive, NB.positive_review_count)

        if predictionN > predictionP:
            status = 'Negative'
        else:
            status = 'Positive'
        # if predictionN > predictionP:
        #     variable = predictionN - (predictionN * 0.05)
        #     if variable < predictionP:
        #         status = 'Neutral'
        #     else:
        #         status = 'Negative'
        # else:
        #     variable = predictionP - (predictionP * 0.05)
        #     if variable > predictionP:
        #         status = 'Neutral'
        #     else:
        #         status = 'Positive'
        comment = Comment(request.form['comment'], status, id, request.form['userId'])
        s.add(comment)
        s.commit()
        flash('Thanks for post')

    comment = s.query(Comment).filter(Comment.post_id == id)
    return render_template('blogPost.html', post=post,user=user, comment=comment)


@app.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.confirmed:
        return redirect('login')
    flash('Please confirm your account!', 'warning')
    return render_template('unconfirmed.html')


@app.route('/resend')
@login_required
def resend_confirmation():
    token = generate_confirmation_token(current_user.email)
    confirm_url = url_for('confirm_email', token=token, _external=True)
    html = render_template('activate.html', confirm_url=confirm_url)
    subject = "Please confirm your email"
    send_email(current_user.email, subject, html)
    flash('A new confirmation email has been sent.', 'success')
    return html



#add new post with parameters title, body
#add parameters to the post table
@app.route('/add', methods=['GET', 'POST'])
@login_required
@check_confirmed
def add_new_post():
    filename = None  # default

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        # print(body.rsplit('?', 1)[0])
        file = request.files['file']
        drop_down = request.form['userId']

        # Save uploaded file on server if it exists and is valid
        if 'file' not in request.files:
            flash('No file part')

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file_path = UPLOAD_DIR + "/" + filename
            size = os.path.getsize(file_path)
            if size > app.config['MAX_CONTENT_LENGTH']:
                return render_template('createNew.html')

        # check if is correct input name in web form
        print(title, " ", body, " ", filename)

        # TO DO create better validator
        # if title or body is null do not add to db
        if (title is not None) and (body is not None):
            print("True")

            Session = sessionmaker(bind=engine)
            s = Session()
            post = Post(request.form['title'], request.form['body'], filename, request.form['userId'])

            s.add(post)
            s.commit()
            flash('Thanks for post')
        else:
            flash('Error: All fields are required!!!')
    return render_template('createNew.html')

if __name__ == '__main__':
    app.run()
