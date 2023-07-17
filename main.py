from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, SubmitField
from wtforms.validators import DataRequired, URL, Email, ValidationError
from flask_ckeditor import CKEditor, CKEditorField
import smtplib
from datetime import datetime as dt
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_gravatar import Gravatar
from functools import wraps

# ~~~~~~~~~~~~~~~~~ APP CONFIGURATION ~~~~~~~~~~~~~~~~~
app = Flask(__name__)
# Input your own
app.config['SECRET_KEY'] = YOUR SECRET KEY
ckeditor = CKEditor(app)
Bootstrap(app)

# ~~~~~~~~~~~~~~~~~ CREATING/LOADING DATABASE ~~~~~~~~~~~~~~~~~
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
db = SQLAlchemy(app)

# ~~~~~~~~~~~~~~~~~ LOGIN MANAGER ~~~~~~~~~~~~~~~~~
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ~~~~~~~~~~~~~~~~~ ADMIN DECORATOR ~~~~~~~~~~~~~~~~~
# Admin is the first user added to the database
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if current_user.id != 1:
                return abort(403)
        except AttributeError:
            return abort(403)
        else:
            return f(*args, **kwargs)
    return decorated_function


# ~~~~~~~~~~~~~~~~~ AVATAR CREDENTIALS~~~~~~~~~~~~~~~~~
gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)

# ~~~~~~~~~~~~~~ EMAIL CREDENTIALS ~~~~~~~~~~~~~~
# Input your own
S_EMAIL = SENDER EMAIL
PASSWORD = SENDER PASSWORD
R_EMAIL = RECEIVER EMAIL

# ~~~~~~~~~~~~~~ HASHING CREDENTIALS ~~~~~~~~~~~~~~
H_METHOD = "pbkdf2:sha256"
S_LENGTH = 8


# ~~~~~~~~~~~~~~ FUNCTION ~~~~~~~~~~~~~~
def send_email(name, email_address, phone_number, message):
    """A function that sends an email to and from specified email addresses using the form data."""
    connection = smtplib.SMTP("smtp.gmail.com", port=587)
    connection.starttls()
    connection.login(user=S_EMAIL, password=PASSWORD)
    if phone_number:
        connection.sendmail(
            from_addr=S_EMAIL,
            to_addrs=R_EMAIL,
            msg="Subject: Fan Mail\n\n"
                f"Name: {name}\n"
                f"Email: {email_address}\n"
                f"Phone Number: {phone_number}\n"
                f"Message: {message}\n")
    else:
        connection.sendmail(
            from_addr=S_EMAIL,
            to_addrs=R_EMAIL,
            msg="Subject: Fan Mail\n\n"
                f"Name: {name}\n"
                f"Email: {email_address}\n"
                f"Message: {message}\n")


# ~~~~~~~~~~~~~~~~~ CONFIGURING DATABASE TABLES  ~~~~~~~~~~~~~~~~~
# Table of All Users
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)

    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="author")

# Table of all Blog Posts
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    comments = relationship("Comment", back_populates="parent_post")

# Table of All Comments
class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="comments")

    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")

    text = db.Column(db.String(250), nullable=False)

# Only use the code below once to create the database tables:
# with app.app_context():
#     db.create_all()


# ~~~~~~~~~~~~~~~~~ CONFIGURING WTFORMS ~~~~~~~~~~~~~~~~~
# Form for Creating a Post
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


# Custom Validator
def validate_phone(form, field):
    for number in str(field.data):
        if str(number) not in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '+']:
            raise ValidationError('Invalid Phone Number')


# Form for Contacting the Owner of the Blog
class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email_address = StringField("Email Address", validators=[DataRequired(), Email()])
    phone_number = StringField("Phone Number", validators=[validate_phone])
    message = TextAreaField("Message", render_kw={'class': 'form-control', 'rows': 10}, validators=[DataRequired()])
    send_button = SubmitField("Send")


# Form for Registering User
class RegisterForm(FlaskForm):
    email = StringField("Email Address", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    register_button = SubmitField("Register")

# Form for Logging in User
class LoginForm(FlaskForm):
    email = StringField("Email Address", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    login_button = SubmitField("Login")

# Form for Commenting on a Post
class CommentForm(FlaskForm):
    comment = CKEditorField("Comment", validators=[DataRequired()])
    submit_button = SubmitField("Submit Comment")


# ~~~~~~~~~~~~~~~~~ ROUTES ~~~~~~~~~~~~~~~~~

# Main Page
@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts, current_user=current_user)


# Register Page
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if db.session.query(User).filter_by(email=form.email.data).first():
            flash("User Already Exists with This Email. Log In Instead.")
            return redirect(url_for('login'))
        else:
            password = generate_password_hash(form.password.data, H_METHOD, S_LENGTH)

            new_user = User()
            new_user.email = form.email.data
            new_user.password = password
            new_user.name = form.name.data

            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)

            return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=form, current_user=current_user)


# Login Page
@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_to_check = db.session.query(User).filter_by(email=form.email.data).first()
        if not user_to_check:
            flash("No Account with This Email. Register Instead.")
            return redirect(url_for('register'))
        elif check_password_hash(user_to_check.password, form.password.data):
            login_user(user_to_check)
            return redirect(url_for('get_all_posts'))
        else:
            flash("Incorrect Password. Please Try Again")
            return render_template("login.html", form=form, current_user=current_user)
    else:
        return render_template("login.html", form=form, current_user=current_user)


# Logout Page
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


# Post Page
@app.route("/post/<int:index>", methods=["GET", "POST"])
def show_post(index):
    form = CommentForm()
    requested_post = db.get_or_404(BlogPost, index)

    if form.validate_on_submit():
        new_comment = Comment(
            author=current_user,
            parent_post=requested_post,
            text=form.comment.data
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('show_post', index=index))
    return render_template("post.html", post=requested_post, form=form, current_user=current_user)


# New Post Page
@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_blog = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            author=current_user,
            img_url=form.img_url.data,
            date=dt.today().strftime("%B %d, %Y")
        )
        db.session.add(new_blog)
        db.session.commit()
        return redirect(url_for('get_all_posts'))
    else:
        return render_template("make-post.html", form=form, current_user=current_user)


# Edit Post Page
@app.route("/edit-post/<post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=current_user,
        body=post.body
                        )
    if form.validate_on_submit():
        post.title = form.title.data
        post.subtitle = form.subtitle.data
        post.body = form.body.data
        post.img_url = form.img_url.data
        db.session.commit()
        return redirect(url_for("show_post", index=post.id))
    return render_template("make-post.html", form=form, edit=True, current_user=current_user)


# Delete Page
@app.route("/delete/<post_id>")
@admin_only
def delete(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    comments_to_delete = db.session.query(Comment).filter_by(post_id=post_id)
    for comment in comments_to_delete:
        db.session.delete(comment)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


# About Page
@app.route("/about")
def about():
    return render_template("about.html", current_user=current_user)


# Contact Page
@app.route("/contact", methods=["POST", "GET"])
def contact_page():
    if current_user.is_authenticated:
        contact_form = ContactForm(
            name=current_user.name,
            email_address=current_user.email,
                        )
    else:
        contact_form = ContactForm()

    if contact_form.validate_on_submit():
        send_email(
            name=contact_form.name.data,
            email_address=contact_form.email_address.data,
            phone_number=contact_form.phone_number.data,
            message=contact_form.message.data)
        return render_template("contact.html", form=contact_form, request_type="POST", current_user=current_user)
    else:
        return render_template("contact.html", form=contact_form, request_type="GET", current_user=current_user)


if __name__ == "__main__":
    app.run(debug=True)
