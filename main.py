from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, URL, Email, ValidationError
from flask_ckeditor import CKEditor, CKEditorField
import smtplib
from datetime import datetime as dt

# ~~~~~~~~~~~~~~~~~ APP CONFIGURATION ~~~~~~~~~~~~~~~~~
app = Flask(__name__)
# Input your own
app.config['SECRET_KEY'] = YOUR OWN SECRET KEY
ckeditor = CKEditor(app)
Bootstrap(app)

# ~~~~~~~~~~~~~~~~~ CREATING/LOADING DATABASE ~~~~~~~~~~~~~~~~~
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(app)

# ~~~~~~~~~~~~~~ EMAIL CREDENTIALS ~~~~~~~~~~~~~~
# Input your own
S_EMAIL = SENDER_EMAIL
PASSWORD = PASSWORD FOR SENDER_EMAIL
R_EMAIL = RECEIVING_EMAIL


# ~~~~~~~~~~~~~~ FUNCTION ~~~~~~~~~~~~~~
def send_email(name, email_address, phone_number, message):
    """A function that sends an email to and from specified email addresses using the form data."""
    connection = smtplib.SMTP("smtp.gmail.com", port=587)
    connection.starttls()
    connection.login(user=S_EMAIL, password=PASSWORD)
    connection.sendmail(
        from_addr=S_EMAIL,
        to_addrs=R_EMAIL,
        msg="Subject: Fan Mail\n\n"
            f"Name: {name}\n"
            f"Email: {email_address}\n"
            f"Phone Number: {phone_number}\n"
            f"Message: {message}\n"
    )


# ~~~~~~~~~~~~~~~~~ CONFIGURING DATABASE TABLE ~~~~~~~~~~~~~~~~~
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


# ~~~~~~~~~~~~~~~~~ CONFIGURING WTFORMS ~~~~~~~~~~~~~~~~~
# Form for Creating a Post
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    author = StringField("Your Name", validators=[DataRequired()])
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
    phone_number = StringField("Phone Number", validators=[DataRequired(), validate_phone])
    message = TextAreaField("Message", render_kw={'class': 'form-control', 'rows': 10}, validators=[DataRequired()])
    send_button = SubmitField("Send")


# ~~~~~~~~~~~~~~~~~ ROUTES ~~~~~~~~~~~~~~~~~

# Main Page
@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts)


# Post Page
@app.route("/post/<int:index>")
def show_post(index):
    requested_post = db.get_or_404(BlogPost, index)
    return render_template("post.html", post=requested_post)


# New Post Page
@app.route("/new-post", methods=["GET", "POST"])
def new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_blog = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            author=form.author.data,
            img_url=form.img_url.data,
            date=dt.today().strftime("%B %d, %Y")
        )
        db.session.add(new_blog)
        db.session.commit()
        return redirect(url_for('get_all_posts'))
    else:
        return render_template("make-post.html", form=form)


# Edit Post Page
@app.route("/edit-post/<post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
                        )
    if form.validate_on_submit():
        post.title = form.title.data
        post.subtitle = form.subtitle.data
        post.body = form.body.data
        post.author = form.author.data
        post.img_url = form.img_url.data
        db.session.commit()
        return redirect(url_for("show_post", index=post.id))
    return render_template("make-post.html", form=form, edit=True)


# Delete Page
@app.route("/delete/<post_id>")
def delete(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


# About Page
@app.route("/about")
def about():
    return render_template("about.html")


# Contact Page
@app.route("/contact", methods=["POST", "GET"])
def contact_page():
    contact_form = ContactForm()
    if contact_form.validate_on_submit():
        send_email(
            name=contact_form.name.data,
            email_address=contact_form.email_address.data,
            phone_number=contact_form.phone_number.data,
            message=contact_form.message.data)
        return render_template("contact.html", form=contact_form, request_type="POST")
    else:
        return render_template("contact.html", form=contact_form, request_type="GET")


if __name__ == "__main__":
    app.run(debug=True)
