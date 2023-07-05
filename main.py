from flask import Flask, render_template, request
import requests
import smtplib

app = Flask(__name__)

# ~~~~~~~~~~~~~~   JSON with Blog Posts' Data ~~~~~~~~~~~~~~
# On https://www.npoint.io/ create your own JSON database using the format below
# [
#    {
#       "id":1,
#       "body":"Example Text of Blog Post.",
#       "date":"June 15, 2023",
#       "title":"Example Title of Blog Post",
#       "author":"Author Name",
#       "subtitle":"Example Subtitle of Blog Post"
#     },
#    ..........
# ]
NPOINT_URL = YOUR_NPOINT_URL
POSTS_DATA = requests.get(NPOINT_URL).json()

# ~~~~~~~~~~~~~~ EMAIL CREDENTIALS ~~~~~~~~~~~~~~
# Input Necessary Credentials
S_EMAIL = SENDER_EMAIL
PASSWORD = PASSWORD_FOR_SENDER_EMAIL
R_EMAIL = RECEIVER_EMAIL


# ~~~~~~~~~~~~~~ FUNCTION ~~~~~~~~~~~~~~
def send_email(message_data):
    """A function that sends an email to and from specified email addresses using the form data."""
    connection = smtplib.SMTP("smtp.gmail.com", port=587)
    connection.starttls()
    connection.login(user=S_EMAIL, password=PASSWORD)
    connection.sendmail(
        from_addr=S_EMAIL,
        to_addrs=R_EMAIL,
        msg="Subject: Fan Mail\n\n"
            f"Name: {message_data['name']}\n"
            f"Email: {message_data['email_address']}\n"
            f"Phone Number: {message_data['phone_number']}\n"
            f"Message: {message_data['message']}\n"
    )

# Main Page of Blog
@app.route("/")
def main_page():
    return render_template("index.html", posts_info=POSTS_DATA)

# About Page of Blog
@app.route("/about")
def about_page():
    return render_template("about.html")

# Contact Page of Blog
@app.route("/contact", methods=["POST", "GET"])
def contact_page():
    if request.method == "POST":
        send_email(request.form)
        return render_template("contact.html", request_type=request.method)
    else:
        return render_template("contact.html", request_type=request.method)

# Post Pages of Blog
@app.route("/<post_number>")
def post_page(post_number):
    return render_template("post.html", post_info=POSTS_DATA[int(post_number) - 1])


if __name__ == "__main__":
    app.run(debug=True)
