from logging import NullHandler
from flask import Flask, jsonify, render_template, url_for, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from authlib.integrations.flask_client import OAuth

import os, json

# App Initialization
app = Flask(__name__)
oauth = OAuth(app)
app.secret_key = 'random secret'

# Authentication Code
google = oauth.register(
    name='google',
    client_id=os.read(os.open("CLIENT_ID", os.O_RDONLY), 100),
    client_secret=os.read(os.open("SECRET", os.O_RDONLY), 100),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',  # This is only needed if using openId to fetch user info
    client_kwargs={'scope': 'openid email profile'},
)

@app.route('/login')
def login():
    google = oauth.create_client('google')
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    token = google.authorize_access_token()
    resp = google.get('userinfo', token=token)
    user_info = resp.json()
    session['email'] = user_info
    return redirect('/')

@app.route('/logout')
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect('/')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(app)

# DB and DB updating code
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    imageLink = db.Column(db.String(50), nullable=True, default="No Provided Image")
    plantName = db.Column(db.String(30), nullable=True, default="Unknown Plant")
    title = db.Column(db.String(100), nullable=True, default=("Post number" + id))
    description = db.Column(db.Text, nullable=True, default="No Description Provided")
    author = db.Column(db.String(30), nullable=True, default='Anonymous')
    location = db.Column(db.String(30), nullable=True, default='Location not Specified')
    date_posted = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)

    def __repr__(self):
        return 'Post ' + str(self.id)

@app.route('/home')
@app.route('/')
def index():
    email = dict(session).get('email', None)
    return render_template('index.html', user = email)

@app.route('/newpost', methods=['GET', 'POST'])
def newPost():
    if request.method == 'POST':
        email = dict(session).get('email', None)
        image_link =      request.form.get('imageLink', False)
        plant_Name =      request.form.get('plantName', False)
        post_title =      request.form.get('title', False)
        post_content =    request.form.get('description', False)
        post_location =   request.form.get('location', False)
        if email is str:
            post_author = email
        else:
            post_author = "Anonymous"

        new_post = Post(title=post_title, description=post_content, location=post_location, plantName=plant_Name, imageLink=image_link, author=post_author)
        db.session.add(new_post)
        db.session.commit()
        return redirect('/allposts')
    else:
        all_posts = Post.query.order_by(Post.date_posted).all()
        return render_template('newpost.html', posts=all_posts)


@app.route('/allposts', methods=['GET'])
def allPosts():
    all_posts = Post.query.order_by(Post.date_posted).all()
    return render_template('allPosts.html', posts=all_posts)


@app.route('/home/<string:name>')
def hello(name):
    return "Hello, " + name


@app.route('/allposts/delete/<int:id>')
def delete(id):
    post = Post.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    return redirect('/allposts')

@app.route('/allposts/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    post = Post.query.get_or_404(id)
    if request.method == 'POST':
        post.title = request.form.get('title')
        post.description = request.form.get('description')
        post.author = request.form.get('author')
        db.session.commit()
        return redirect('/allposts')
    else:
        return render_template('edit.html', post=post)

app.config["IMAGE_UPLOADS"] = "~/Projects/PlantApp"
@app.route("/newpost", methods=["GET", "POST"])
def upload_image():
    if request.method == "POST":
        if request.files:
            image = request.files["image"]
            print(image)
            image.save(os.path.join(app.config["IMAGE_UPLOADS"], image.filename))
            print("Image saved")
            return redirect(request.url)
    return render_template("index.html")


# Run in debug mode if not deployed
if __name__ == "__main__":
    app.run(debug=True)