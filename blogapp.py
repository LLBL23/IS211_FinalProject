import sqlite3
from functools import wraps
from flask import Flask, session, redirect, url_for, render_template, flash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, EqualTo
from wtforms.widgets import TextArea
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config['SECRET_KEY'] = "secret key"


def connect_db():
    connection = sqlite3.connect('blogs.db')
    return connection


def get_db_connection():
    conn = sqlite3.connect('blogs.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    con = connect_db()
    with open('schema.sql', mode='r') as f:
        con.executescript(f.read())
        con.commit()
        con.close()
        print("database initialized")


def login_required(test):
    @wraps(test)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return test(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))
    return wrap

# Store Current User Info
current_user = []


# Create Add Post Page
@app.route('/add-post', methods=['GET', 'POST'])
@login_required
def add_post():
    form = PostForm()
    current_user_str = str(current_user[0])
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        author = form.author.data
        slug = form.slug.data
        to_add = (title, content, author, slug, current_user_str)


        # Clear The Form
        form.title.data = ''
        form.content.data = ''
        form.author.data = ''
        form.slug.data = ''

        # Add Post To Database
        conn = get_db_connection()
        conn.execute("INSERT INTO posts (title, content, author, slug, users_id) VALUES (?, ?, ?, ?, ?)", to_add)
        conn.commit()
        flash('Blog post submitted successfully!')
        return redirect(url_for('index'))

    return render_template('add_post.html', form=form)


# Create Add User Page
@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
    name = None
    form = UserForm()
    conn = get_db_connection()
    if form.validate_on_submit():
        email = [form.email.data]
        cur_7 = conn.execute("SELECT * FROM users WHERE email = ? LIMIT 1", email).fetchall()
        user = cur_7
        if user == []:
            # Hash the password
            hashed_pw = generate_password_hash(form.password_hash.data, "sha256")
            print(hashed_pw)
            add_user = form.name.data, form.username.data, form.email.data, hashed_pw
            cur_8 = conn.execute("INSERT INTO users (name, username, email, password_hash) VALUES (?, ?, ?, ?)", add_user)
            conn.commit()
            flash("Registration Successful!")
        name = form.name.data

        # Clear The Form
        form.name.data = ''
        form.username.data = ''
        form.email.data = ''
        form.password_hash.data = ''
    cur_9 = conn.execute("SELECT * FROM users ORDER BY date_added").fetchall()
    our_users = cur_9
    return render_template('add_user.html', form=form, name=name, our_users=our_users)


# Create Password Check Page
@app.route('/check_pw', methods=['GET', 'POST'])
def check_pw():
    email = None
    password = None
    pw_to_check = None
    passed = None
    form = PasswordForm()
    conn = get_db_connection()

    # Validate Form
    if form.validate_on_submit():
        email = [form.email.data]
        password = [form.password_hash.data]

        form.email.data = ''
        form.password_hash.data = ''

        # Lookup User By Email Address
        cur_13 = conn.execute("SELECT * FROM users WHERE email = ? LIMIT 1", email).fetchall()
        for row in cur_13:
            pw_to_check = [row[0], row[1], row[2], row[3], row[4]]

            # Check Hashed Password
            passed = check_password_hash(pw_to_check[4], password[0])

    return render_template("check_pw.html", email=email, password=password, pw_to_check=pw_to_check, passed=passed, form=form)


# Create Dashboard Page
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    id_to_lookup = [str(current_user[0])]
    # Get Current User's Blogs from Database
    conn = get_db_connection()
    cur_16 = conn.execute("SELECT * FROM posts WHERE users_id = ?", id_to_lookup).fetchall()
    if cur_16 is None:
        flash("You Have Not Created Any Posts!")
        return render_template('dashboard.html')
    else:
        user_posts = cur_16
        form = PostForm()
        current_user_str = str(current_user[0])
        if form.validate_on_submit():
            title = form.title.data
            content = form.content.data
            author = form.author.data
            slug = form.slug.data
            to_add = (title, content, author, slug, current_user_str)

            # Clear The Form
            form.title.data = ''
            form.content.data = ''
            form.author.data = ''
            form.slug.data = ''

            # Add Post To Database
            conn = get_db_connection()
            conn.execute("INSERT INTO posts (title, content, author, slug, users_id) VALUES (?, ?, ?, ?, ?)", to_add)
            conn.commit()
            flash('Blog post submitted successfully!')
            return redirect(url_for('index'))

    return render_template('dashboard.html', user_posts=user_posts, form=form)


# Create Delete User Page
@app.route('/delete/<int:id>')
@login_required
def delete(id):
    id_to_delete = str(id)
    name = None
    form = UserForm()
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM users WHERE id = ?", id_to_delete).fetchall()
        conn.commit()
        flash("User Deleted Successfully!")
        cur_13 = conn.execute("SELECT * FROM users ORDER BY date_added").fetchall()
        our_users = cur_13
        return render_template('add_user.html', form=form, name=name, our_users=our_users)
    except:
        flash("There was a problem deleting user, try again...")
        return render_template('add_user.html', form=form, name=name, our_users=our_users)


# Create Delete Post Page
@app.route('/posts/delete/<int:id>')
@login_required
def delete_post(id):
    id_str = str(id)
    form = PostForm()
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM posts WHERE id = ?", id_str).fetchall()
        conn.commit()

        # Return a message
        flash('Blog Post Was Deleted!')
        # Grab all posts from the database
        cur_1 = conn.execute("SELECT * FROM posts ORDER BY date_posted").fetchall()
        posts = cur_1
        return render_template('posts.html', posts=posts)

    except:
        flash('There was a problem deleting post, try again...')
        cur_3 = conn.execute("SELECT * FROM posts ORDER BY date_posted").fetchall()
        posts = cur_3
        return render_template('posts.html', posts=posts)


# Create Edit Post Page
@app.route('/posts/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    id_int = int(id)
    form = PostForm()

    post_title = ''
    post_content = ''
    post_author = ''
    post_slug = ''
    conn = get_db_connection()
    cur_6 = conn.execute("SELECT * FROM posts WHERE id = ?", id).fetchall()
    post = cur_6
    for row in post:
        post_title = row[1]
        post_content = row[2]
        post_author = row[3]
        post_slug = row[5]

    if form.validate_on_submit():
        edit_title = form.title.data
        edit_author = form.author.data
        edit_slug = form.slug.data
        edit_content = form.content.data
        entry = (edit_title, edit_content, edit_author, edit_slug, id_int)
        print(entry)
        # Update database
        conn = get_db_connection()
        conn.execute("UPDATE posts SET title = ?, content = ?, author = ?, slug = ? WHERE id = ?;", entry)
        conn.commit()

        flash('Post has been updated!')
        return redirect(url_for('posts', id=id_int))

    form.title.data = post_title
    form.author.data = post_author
    form.slug.data = post_slug
    form.content.data = post_content
    return render_template('edit_post.html', form=form)


# Create Index Page
@app.route('/')
def index():
    return redirect(url_for('posts'))


# Create Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    user = []
    conn = get_db_connection()
    if form.validate_on_submit():
        username_to_search = [form.username.data]
        cur_15 = conn.execute("SELECT * FROM users WHERE username = ? LIMIT 1", username_to_search).fetchall()
        for row in cur_15:
           user = row[0], row[1], row[2], row[3], row[4], row[5]
        if user != []:
            # Check the hash
            if check_password_hash(user[5], form.password.data):
                session['logged_in'] = True
                flash("Login Successful!")
                return redirect(url_for('dashboard')), current_user.append(user[0])
            else:
                flash("Wrong Password - Try Again!")
        else:
            flash("That User Doesn't Exist! Try Again...")

    return render_template('login.html', form=form)


# Create logout Page
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    session.clear()
    current_user.clear()
    flash("You have been logged out!")
    return redirect(url_for('login'))


# Create Post Page
@app.route('/posts/<int:id>')
@login_required
def post(id):
    id_str = str(id)
    conn = get_db_connection()
    cur_5 = conn.execute("SELECT * FROM posts WHERE id = ?", id_str).fetchall()
    for row in cur_5:
        row = row

    return render_template('post.html', row=row)


# Create Posts Page
@app.route('/posts')
def posts():
    # Grab all posts from the database
    conn = get_db_connection()
    cur_4 = conn.execute("SELECT * FROM posts ORDER BY date_posted DESC").fetchall()
    for row in cur_4:
        posts = cur_4

    return render_template('posts.html', posts=posts)


# Create Login Form
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")


# Create Post Form
class PostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    content = StringField("Content", validators=[DataRequired()], widget=TextArea())
    author = StringField("Author", validators=[DataRequired()])
    slug = StringField("Slug", validators=[DataRequired()])
    submit = SubmitField("Submit")


# Create User Form
class UserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password_hash = PasswordField("Password", validators=[DataRequired(), EqualTo('password_hash2', message='Password Must Match!')])
    password_hash2 = PasswordField("Confirm Password", validators=[DataRequired()])
    submit = SubmitField("Submit")




if __name__ == '__main__':
    app.run(debug=True)