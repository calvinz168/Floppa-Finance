import os
import secrets

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from PIL import Image

from flasksite import app, bcrypt, db
from flasksite.forms import (LoginForm, PostForm, RegistrationForm,
                             UpdateAccountForm,CommentForm,QuizForm)
from flasksite.models import Post, User, Comment


@app.route("/")
@app.route("/home")
def home():
    posts = Post.query.all()
    return render_template('home.html', posts=posts)

@app.route("/about")
def about():
    return render_template('about.html')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, score=0)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


@app.route("/payingBills", methods=['GET', 'POST'])
@login_required
def paying_bills():
    return render_template('paying_bills.html', title='Paying Bills')


@app.route("/childEduSavings", methods=['GET', 'POST'])
@login_required
def child_edu():
    score = current_user.score
    return render_template('child_edu.html', title='Child Education Savings',score=score)


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post',
                           form=form, legend='New Post')


@app.route("/post/<int:post_id>/comment", methods=["GET", "POST"])
@login_required
def comment_post(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    #user_id = User.query.get(current_user.id)
    if request.method == 'POST': # this only gets executed when the form is submitted and not when the page loads
        if form.validate_on_submit():
            comment = Comment(content=form.body.data, post_id=post.id, user_id=current_user.id)
            db.session.add(comment)
            db.session.commit()
            flash("Your comment has been added to the post", "success")
            return redirect(url_for("post", post_id=post.id))
    return render_template("create_comment.html", title="Comment Post", form=form, post_id=post_id)


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get(post_id)
    comments = Comment.query.filter_by(post_id=post_id).all()
    return render_template('post.html', title=post.title, post=post, comments=comments)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post')


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))


@app.route('/test', methods=['POST', 'GET'])
def test():
    form = QuizForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            print("form.example.data",form.example.data)
        else:
            print("form.errors",form.errors)
    print("ASD")
    return render_template('htmltest.html', form=form)


@app.route('/pbQuiz',methods=['POST','GET'])
@login_required
def pbQuiz():
    form = QuizForm()
    q1w = True
    q2w = True

    if request.method == 'POST':
        button = False
        marks = 0
        print("current_user.score",current_user.score)
        if form.validate_on_submit():
            print("form.q1.data",form.q1.data)
            print("form.q2.data",form.q2.data)
            if form.q1.data == "q1value4":
                current_user.score += 10
                marks += 1
                q1w = False
            if form.q2.data == "q2value2":
                current_user.score += 10
                marks += 1
                q2w = False
            db.session.commit()
            if marks > 1:
                flash(f"Congratulations! You have scored {marks}/2", "success")
            else:
                flash(f"You have scored {marks}/2", "danger")
        else:
            print("form.errors",form.errors)
    if request.method == "GET":
        button =  True


    print("current_user.score",current_user.score)
    return render_template('paying_bills_quiz.html', form=form, butt=button,q1w=q1w,q2w=q2w)