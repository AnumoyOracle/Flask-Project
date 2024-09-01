from flask import Flask, redirect, render_template, request, session, flash, url_for
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os
from werkzeug.utils import secure_filename
import math

app = Flask(__name__)
app.secret_key = "my-secret-key"

file = open("config.json", "r")
file_data = json.load(file)
params = file_data["params"]

local_server = params["local_server"]

# Configure MySQL Database URI for Flask-SQLAlchemy
if local_server == True:
    app.config["SQLALCHEMY_DATABASE_URI"] = params["local_uri"]
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params["prod_uri"]

# Suppress SQLAlchemy track modifications warning
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = params["upload_base_uri"]

# Configuration for mailing others

app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    # MAIL_USE_TLS=True,
    MAIL_USERNAME=params["gmail_username"],
    MAIL_PASSWORD=params["gmail_password"],
)

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Initialize Mail app
mail = Mail(app)


# Define a new model for Post
class Post(db.Model):
    post_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    slug = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<Post {self.title}>"


# Define a new model for Contact
class Contact(db.Model):
    contact_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    phone_num = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    msg = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"<Contact {self.name}>"


@app.route("/")
def home():

    posts = Post.query.all()
    last_page = math.ceil(len(posts) / params["limit_of_posts"])
    page = request.args.get("page")

    if not str(page).isnumeric():
        page = 1
    page = int(page)

    posts = posts[
        (page - 1) * params["limit_of_posts"] : (page - 1) * params["limit_of_posts"]
        + params["limit_of_posts"]
    ]
    # Pagination Logic
    # First Page
    if page == 1:
        prev = "#"
        next = "/?page=" + str(page + 1)
    # Middle Page
    elif page != 1 and page != last_page:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)
    # Last Page
    else:
        prev = "/?page=" + str(page - 1)
        next = "#"

    return render_template(
        "index.html", params=params, posts=posts, prev=prev, next=next, page = page, last_page = last_page
    )


@app.route("/about")
def about():
    return render_template("about.html", params=params)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        message = request.form.get("message")

        new_contact = Contact(
            name=name, email=email, phone_num=phone, msg=message, date=datetime.now()
        )
        db.session.add(new_contact)
        db.session.commit()
        print("New contact added successfully ........")

        mail.send_message(
            "New message from : " + name,
            sender=email,
            recipients=params["recipients"],
            body=message + " " + phone,
        )
        flash("Mail has been sent successfully on behalf of you ...", "success")
    return render_template("contact.html", params=params)


@app.route("/post")
def post():
    return render_template("post.html", params=params)


# Define allowed file extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/add-post", methods=["GET", "POST"])
def add_post():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        slug = request.form.get("slug")
        file = request.files.get("image_url")

        print(file.filename)

        if file and file.filename != "" and allowed_file(file.filename):
            filename = secure_filename(file.filename)  # Secure the filename
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)  # Save the file to the specified path
            print("Image uploaded successfully ......")
        else:
            filename = "post-bg.jpg"

        # Create a new post
        new_post = Post(
            title=title,
            content=content,
            slug=slug,
            date=datetime.now(),
            image_url=filename,
        )

        db.session.add(new_post)
        db.session.commit()

        print("New post added successfully ........")
        flash("Post has been added successfully", "success")

    return render_template("add_post.html", params=params)


@app.route("/edit-post/<string:post_id>", methods=["GET", "POST"])
def edit_post(post_id):

    post = Post.query.filter_by(post_id=post_id).first()
    # print(post)

    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        slug = request.form.get("slug")
        file = request.files.get("image_url")
        date = datetime.now()

        post.title = title
        post.content = content
        post.slug = slug
        post.date = date

        if file and file.filename != "" and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)
            post.image_url = filename

        db.session.commit()
        all_posts = Post.query.all()
        flash("Post has been edited successfully", "warning")
        return render_template("dashboard.html", params=params, posts=all_posts)

    return render_template("edit_post.html", params=params, post=post)


@app.route("/delete-post/<string:post_id>")
def delete_post(post_id):
    post = Post.query.filter_by(post_id=post_id).first()
    db.session.delete(post)
    db.session.commit()
    print("Post deleted successfully")
    flash("Post has been removed successfully", "danger")
    posts = Post.query.all()
    return render_template("dashboard.html", params=params, posts=posts)


@app.route("/post/<string:post_slug>", methods=["GET"])
def post_with_slug(post_slug):
    post = Post.query.filter_by(slug=post_slug).first()
    print(post.image_url)
    return render_template("post.html", post=post, params=params)


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():

    if "user" in session and session["user"] == params["admin_username"]:
        posts = Post.query.all()
        return render_template("dashboard.html", params=params, posts=posts)

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if (
            username == params["admin_username"]
            and password == params["admin_password"]
        ):
            session["user"] = username
            posts = Post.query.all()
            return render_template("dashboard.html", params=params, posts=posts)

    return render_template("login.html", params=params)


@app.route("/logout")
def logout():
    session.pop("user")
    print("You have logged out of the website successfully")
    posts = Post.query.all()
    return redirect(url_for("home"))
    # return render_template("contact.html", params=params)


if __name__ == "__main__":

    # Run Flask application
    app.run(debug=True)
