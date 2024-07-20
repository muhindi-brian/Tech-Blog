from flask import render_template, url_for, flash, redirect, request
from app import app, mysql
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FileField
from wtforms.validators import DataRequired, Email, EqualTo
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
import re
import os
from werkzeug.utils import secure_filename

# Configuration
# UPLOAD_FOLDER = 'static/uploads'
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    """Load user from database by ID."""
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    cursor.close()
    return User(user) if user else None

class User(UserMixin):
    def __init__(self, user):
        self.id = user[0]
        self.username = user[1]
        self.email = user[2]
        self.password = user[3]

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    image = FileField('Image')
    submit = SubmitField('Post')

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send')

def generate_slug(title):
    """Generate a URL-friendly slug from a title."""
    slug = re.sub(r'[^\w\s-]', '', title).strip().lower()
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug

@app.route('/')
def index():
    """Render the index page with posts."""
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM posts ORDER BY created_at DESC')
    posts = cursor.fetchall()
    cursor.close()
    return render_template('index.html', posts=posts)

@app.route('/about')
def about():
    """Render the about page."""
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Handle the contact form submission."""
    form = ContactForm()
    if form.validate_on_submit():
        # Here you would typically send an email or store the message in the database
        name = form.name.data
        email = form.email.data
        message = form.message.data

        # For demonstration purposes, let's just flash a message
        flash('Your message has been sent successfully.', 'success')
        return redirect(url_for('contact'))

    return render_template('contact.html', form=form)

@app.route('/post/<slug>')
def post(slug):
    """Render a single post based on slug."""
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM posts WHERE slug = %s', (slug,))
    post = cursor.fetchone()
    cursor.close()
    return render_template('post.html', post=post)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    form = LoginForm()
    if form.validate_on_submit():
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s', (form.email.data,))
        user = cursor.fetchone()
        cursor.close()
        if user and user[3] == form.password.data:  # Note: Use hashed passwords in production
            user_obj = User(user)
            login_user(user_obj)
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    form = RegistrationForm()
    if form.validate_on_submit():
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO users (username, email, password) VALUES (%s, %s, %s)',
                       (form.username.data, form.email.data, form.password.data))
        mysql.connection.commit()
        cursor.close()
        flash('Account created successfully', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    """Render the dashboard page."""
    return render_template('dashboard.html')

@app.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    """Handle creation of a new post."""
    form = PostForm()
    if form.validate_on_submit():
        slug = generate_slug(form.title.data)
        image_url = None
        
        # Handle file upload
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                uploads_dir = os.path.join(app.root_path, UPLOAD_FOLDER)
                os.makedirs(uploads_dir, exist_ok=True)  # Ensure directory exists
                file_path = os.path.join(uploads_dir, filename)
                print(f"Saving file to: {file_path}")
                file.save(file_path)
                image_url = url_for('static', filename=f'uploads/{filename}')
                print(f"Saving file to: {file_path}")
        
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO posts (title, content, slug, author_id, image_url) VALUES (%s, %s, %s, %s, %s)',
                       (form.title.data, form.content.data, slug, current_user.id, image_url))
        mysql.connection.commit()
        cursor.close()
        flash('Post created successfully', 'success')
        return redirect(url_for('index'))
    return render_template('new_post.html', form=form)

@app.route('/edit_post/<slug>', methods=['GET', 'POST'])
@login_required
def edit_post(slug):
    """Handle editing of an existing post."""
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM posts WHERE slug = %s AND author_id = %s', (slug, current_user.id))
    post = cursor.fetchone()
    cursor.close()

    if not post:
        flash('Post not found or you do not have permission to edit it.', 'danger')
        return redirect(url_for('index'))

    form = PostForm(data={'title': post[1], 'content': post[2]})
    if form.validate_on_submit():
        new_slug = generate_slug(form.title.data)
        image_url = post[4]  # Keep existing image URL

        # Handle file upload
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                uploads_dir = os.path.join(app.root_path, UPLOAD_FOLDER)
                os.makedirs(uploads_dir, exist_ok=True)  # Ensure directory exists
                file_path = os.path.join(uploads_dir, filename)
                print(f"Saving file to: {file_path}")
                file.save(file_path)
                image_url = url_for('static', filename=f'uploads/{filename}')
                print(f"Saving file to: {file_path}")
        
        cursor = mysql.connection.cursor()
        cursor.execute('UPDATE posts SET title = %s, content = %s, slug = %s, image_url = %s WHERE id = %s',
                       (form.title.data, form.content.data, new_slug, image_url, post[0]))
        mysql.connection.commit()
        cursor.close()
        flash('Post updated successfully', 'success')
        return redirect(url_for('index'))

    return render_template('edit_post.html', form=form, post=post)

@app.route('/delete_post/<slug>')
@login_required
def delete_post(slug):
    """Handle deletion of a post."""
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM posts WHERE slug = %s AND author_id = %s', (slug, current_user.id))
    mysql.connection.commit()
    cursor.close()
    flash('Post deleted successfully', 'success')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    """Handle user logout."""
    logout_user()
    return redirect(url_for('index'))
