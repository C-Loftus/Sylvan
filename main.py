from flask import Flask, flash, render_template, url_for, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from authlib.integrations.flask_client import OAuth
from werkzeug.utils import secure_filename
import os

# App Initialization and Config
app = Flask(__name__)
app.config["IMAGE_UPLOADS"] = "/home/colton/Projects/PlantApp/static/Images"
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["JPEG", "JPG", "PNG", "GIF"]
app.config["MAX_IMAGE_FILESIZE"] = 0.5 * 1024 * 1024
oauth = OAuth(app)
app.secret_key = 'random secret'

# Authentication Object for OAuth
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
        image_link = ""
        if request.files:
            print("Is a file")
            image = request.files["image"]
            if "filesize" in request.cookies:
                if not allowed_image_filesize(request.cookies["filesize"]):
                    print("Filesize exceeded maximum limit")
                    return redirect(request.url)
            if image.filename == "":
                print("No filename")
            if allowed_image(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config["IMAGE_UPLOADS"], filename))
                print(image)
                image_link = filename
            else:
                print("That file extension is not allowed")
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
    credentials = dict(session).get('email', None)
    if (credentials is not None and credentials is str):
        if (id.author == credentials):
            db.session.delete(post)
            db.session.commit()
            return redirect('/allposts')
    flash("You do not have permission to do that. Try logging in")
    return redirect("/error")

@app.route('/allposts/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    post = Post.query.get_or_404(id)
    if request.method == 'POST':
        credentials = dict(session).get('email', None)
        if (credentials is not None and credentials is str):
            if (id.author == credentials):
                post.title = request.form.get('title')
                post.description = request.form.get('description')
                post.author = request.form.get('author')
                db.session.commit()
                return redirect('/allposts')
        else:
            flash("You do not have permission to do that. Try logging in")
            return redirect('/error')
    else:
        return render_template('edit.html', post=post)

def allowed_image(filename):
    # We only want files with a . in the filename
    if not "." in filename:
        return False
    # Split the extension from the filename
    ext = filename.rsplit(".", 1)[1]
    # Check if the extension is in ALLOWED_IMAGE_EXTENSIONS
    if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else:
        return False

def allowed_image_filesize(filesize):
    
    if int(filesize) <= app.config["MAX_IMAGE_FILESIZE"]:
        return True
    else:
        return False

@app.route('/error')
def handleError():
    return render_template("error.html")

# Run in debug mode if not deployed
if __name__ == "__main__":
    app.run(debug=True)