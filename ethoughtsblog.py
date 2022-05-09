from flask import Flask, render_template, redirect, g, request, session, Markup, url_for
import sqlite3

app = Flask(__name__)
check_username = 'admin'
check_password = 'admin'
app.secret_key = 'finalproject'
DATABASE = 'C:/Users/Jadah/IS211_FinalProject/blog.db'

connection = sqlite3.connect('C:/Users/Jadah/IS211_FinalProject/blog.db')

with open('schema.sql') as s:
    connection.executescript(s.read())

db = connection.cursor()

db.execute('INSERT INTO posts (title, content) VALUES (?, ?)',('Post 1', 'Sample post #1.'))
db.execute('INSERT INTO posts (title, content) VALUES (?, ?)',('Post 2', 'Sample post #2.'))
db.execute('INSERT INTO posts (title, content) VALUES (?, ?)',('Post 3', 'Sample post #3.'))
db.execute('INSERT INTO authors (author_name) VALUES (?)',('Jadah Holly',))
db.execute('INSERT INTO posts_authors VALUES (?, ?)', (1, 1))
db.execute('INSERT INTO posts_authors VALUES (?, ?)', (1, 2))
db.execute('INSERT INTO posts_authors VALUES (?, ?)', (1, 3))

connection.commit()
connection.close()

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.route('/')
def homepage():
    db = get_db()
    blog_posts = g.db.execute('''SELECT posts.title,
                                 posts.publication_date,
                                 posts.content,
                                 authors.author_name,
                                 posts.post_id
                                 FROM posts_authors
                                 INNER JOIN posts on posts_authors.post_id = posts.post_id
                                 INNER JOIN authors on posts_authors.author_id = authors.author_id
                                 WHERE published == 1
                                 ORDER BY posts.publication_date DESC''').fetchall()
    return render_template('homepage.html', blog=blog_posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != check_username:
            error = "Incorrect Username! Please try again"
        elif request.form['password'] != check_password:
            error = 'Invalid Password! Please try again.'
        else:
            session['username'] = check_username
            return redirect('/dashboard')
    return render_template('login.html', error=error)

@app.route('/dashboard', methods=['POST', 'GET'])
def dashboard():
    if not session.get('username'):
        return redirect(url_for('login'))
    db = get_db()
    blog_posts = g.db.execute('''SELECT posts.title,
                              posts.publication_date,
                              posts.content,
                              authors.author_name,
                              posts.post_id,
                              posts.published
                              FROM posts_authors
                              INNER JOIN posts on posts_authors.post_id == posts.post_id
                              INNER JOIN authors on posts_authors.author_id == authors.author_id
                              ORDER BY posts.publication_date DESC''').fetchall()
    return render_template('dashboard.html', blog=blog_posts)

@app.route('/edit_post/<int:post_num>')
def edit_post(post_num):
    if not session.get('username'):
        return redirect(url_for('login'))
    db = get_db()
    post = g.db.execute('''SELECT posts.title,
                        posts.publication_date,
                        posts.content,
                        authors.author_name,
                        posts.post_id,
                        authors.author_id
                        FROM posts_authors
                        INNER JOIN posts on posts_authors.post_id == posts.post_id
                        INNER JOIN authors on posts_authors.author_id == authors.author_id
                        WHERE posts_authors.post_id = ?''', (post_num,)).fetchone()
    return render_template('edit_post.html', post=post)

@app.route('/update_post', methods=['POST', 'GET'])
def update_post():
    if not session.get('username'):
        return redirect(url_for('login'))
    title = request.form.get('title')
    content = request.form.get('content')
    post_num = request.form.get('post_num')
    db = get_db()
    g.db.execute('UPDATE posts '
                 'SET title = ?, '
                 'content = ? '
                 'WHERE post_id = ?', (title, content, post_num),
                 )
    g.db.commit()
    return redirect(url_for('dashboard'))


@app.route('/delete/<int:post_num>')
def delete_post(post_num):
    if not session.get('username'):
        return redirect(url_for('login'))
    db = get_db()
    g.db.execute('DELETE FROM posts WHERE post_id = ?', (post_num,))
    g.db.execute('DELETE FROM posts_authors WHERE post_id = ?', (post_num,))
    g.db.commit()
    return redirect(url_for('dashboard'))


@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if not session.get('username'):
        return redirect(url_for('login'))
    return render_template('create_post.html')


@app.route('/add_post', methods=['POST', 'GET'])
def add_post():
    if not session.get('username'):
        return redirect(url_for('login'))
    title = request.form.get('title')
    content = request.form.get('content')
    author = 1
    db = get_db()
    post_num = g.db.execute('INSERT INTO posts (title, content) VALUES (?,?)', (title, content,)).lastrowid
    g.db.execute('INSERT INTO posts_authors (author_id, post_id) VALUES (?,?)', (author, post_num,))
    g.db.commit()
    return redirect(url_for('dashboard'))

@app.route('/unpublish/<int:post_num>')
def unpublish(post_num):
    if not session.get('username'):
        return redirect(url_for('login'))
    db = get_db()
    g.db.execute('Update posts '
                 'SET published = 0 '
                 'WHERE post_id = ?', (post_num,))
    g.db.commit()
    return redirect(url_for('dashboard'))


@app.route('/publish/<int:post_num>')
def publish(post_num):
    if not session.get('username'):
        return redirect(url_for('login'))
    db = get_db()
    g.db.execute('Update posts '
                 'SET published = 1 '
                 'WHERE post_id =?', (post_num,))
    g.db.commit()
    return redirect(url_for('dashboard'))


@app.route('/<int:post_num>')
def post(post_num):
    db = get_db()
    post = g.db.execute('SELECT * FROM posts WHERE post_id = ?', (post_num,)).fetchone()
    author = g.db.execute('SELECT authors.author_id, '
                          'authors.author_name '
                          'FROM posts_authors '
                          'INNER JOIN authors on posts_authors.author_id == authors.author_id '
                          'WHERE post_id = ?', (post_num,)).fetchone()
    page = Markup("<head><meta charset='UTF-8'></head>" +
                  '<body><h1 align="center">' + post[1] + '</h1><p align="center"><strong>Written by: ' + author[1] +
                  '</strong></p><p align="center"><strong>Date: ' + post[2] + '</strong></p><br><div>' + post[3] +
                  '</div></body>')
    return render_template('post.html', post=page)

if __name__ == "__main__":
    app.run(debug=True)
