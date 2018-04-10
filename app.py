import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, flash, session, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, ValidationError
import requests

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = "super secret key"
Bootstrap(app)

DATABASEURI = os.getenv('DATABASEURI', "postgresql://djb2195:freeslugs@35.196.90.148:5432/proj1part2")
engine = create_engine(DATABASEURI)

@app.before_request
def before_request():
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  try:
    g.conn.close()
  except Exception as e:
    pass

def get_shows(user_id): 
  query = 'SELECT S.tid, S.name, S.description FROM "Users_Shows" AS U INNER JOIN shows AS S ON U.tid = S.tid WHERE U.uid = {0}'.format(user_id)
  cursor = g.conn.execute(query)
  shows = []

  for result in cursor:
    shows.append(result)
  cursor.close()

  return shows

def get_movies(user_id):  
  query = 'SELECT M.name, M.mid FROM "Users_Movies" AS U INNER JOIN movies AS M ON U.mid = M.mid WHERE U.uid = {0}'.format(user_id)
  cursor = g.conn.execute(query)
  print query
  movies = []

  for result in cursor:
    movies.append(result)
  cursor.close()

  return movies

class LoginForm(FlaskForm):
  email = StringField('email', validators=[DataRequired(), Email()])
  password = PasswordField('password', validators=[DataRequired()])
  submit = SubmitField(label='password')

# returns bool 
def login_user(email, password):
  query = "SELECT uid FROM users where email = '{0}' and password = '{1}'".format(email, password)
  cursor = g.conn.execute(query)
  user = cursor.first()
  cursor.close()  
  
  if user is not None:
    # save user id to session
    session['uid'] = user[0]

    return True
  return False

@app.route('/', methods=('GET', 'POST'))
def index():
  form = LoginForm(csrf_enabled=False)
  if form.validate_on_submit():
    if login_user(form.email.data, form.password.data):
      return redirect(url_for('home'))
    else:
      form.email.errors.append("User and password combination is incorrect.")

    if form.errors:
      for error_field, error_message in form.errors.iteritems():
        flash("Field : {field}; error : {error}".format(field=error_field, error=error_message))

  return render_template("index.html", form=form)

@app.route('/logout')
def logout():
  session.pop('username', None)
  return redirect(url_for('index'))

@app.route('/home', methods=('GET', 'POST'))
def home():
  if not 'uid' in session:
    return redirect(url_for('index'))
    pass

  uid = session['uid']
  shows = get_shows(uid)
  movies = get_movies(uid)
  return render_template("home.html", shows=shows, movies=movies)

class SearchForm(FlaskForm):
  query = StringField('query', validators=[DataRequired()])
  type_field = BooleanField('Movie?')
  submit = SubmitField(label='search')

@app.route('/search', methods=('GET', 'POST'))
def search():
  form = SearchForm(csrf_enabled=False)
  results = None
  type_field = None

  if form.validate_on_submit():
    query = form.query.data
    type_field = "movie" if form.type_field.data else "tv"
    # show search results
    url = "https://api.themoviedb.org/3/search/{0}?api_key=55d00e73946f9191a7a20f9ef4277624&language=en-US&page=1&include_adult=false&query={1}".format(type_field, query)
    r = requests.get(url)
    json = r.json()
    results = json['results']

    if form.errors:
      for error_field, error_message in form.errors.iteritems():
        flash("Field : {field}; error : {error}".format(field=error_field, error=error_message))

  return render_template("search.html", form=form, results=results, type_field=type_field)

def find_movie(mid):
  query = "SELECT mid FROM movies where mid = '{0}'".format(mid)
  cursor = g.conn.execute(query)
  movie = cursor.first()
  cursor.close()  
  
  if movie is not None:
    return movie[0]
  return False

@app.route('/add_movie/<id>', methods=('GET', 'POST'))
def add_movie(id):
  # check if id exists in db
  if not find_movie(id):
    # else grab it from api
    url = "https://api.themoviedb.org/3/movie/{0}?api_key=55d00e73946f9191a7a20f9ef4277624&language=en-US".format(id)
    r = requests.get(url)
    json = r.json()
    genre = json['genres'][0]['name']
    description = json['overview'][:200]
    name = json['title']
    # save it 
    sql = "INSERT INTO movies VALUES (%s,%s,%s,%s, NOW(), NOW())"
    params = [id, name, description, genre]
    g.conn.execute(sql, params)
  # add to join table relation
  sql = 'INSERT INTO "Users_Movies" VALUES (%s,%s)'
  params = [id, session['uid']]
  g.conn.execute(sql, params)
  return redirect(url_for('home')) 

def find_show(tid):
  query = "SELECT tid FROM shows where tid = '{0}'".format(tid)
  cursor = g.conn.execute(query)
  show = cursor.first()
  cursor.close()  
  
  if show is not None:
    return show[0]
  return False

@app.route('/add_show/<id>', methods=('GET', 'POST'))
def add_show(id):
  # check if id exists in db
  if not find_show(id):
    # else grab it from api
    url = "https://api.themoviedb.org/3/tv/{0}?api_key=55d00e73946f9191a7a20f9ef4277624&language=en-US".format(id)
    r = requests.get(url)
    json = r.json()
    description = json['overview'][:200]
    name = json['name']
    # save it 
    sql = "INSERT INTO shows VALUES (%s,%s,%s, NOW(), NOW())"
    params = [id, name, description]
    g.conn.execute(sql, params)
  # add to join table relation
  sql = 'INSERT INTO "Users_Shows" VALUES (%s,%s)'
  params = [id, session['uid']]
  g.conn.execute(sql, params)
  return redirect(url_for('home')) 
  
@app.route('/movies/<mid>')
def movie(mid):
  query = "SELECT mid, name, description, genre FROM movies where mid = '{0}'".format(mid)
  cursor = g.conn.execute(query)
  movie = cursor.first()
  cursor.close()  

  return render_template("movie.html", movie=movie)

@app.route('/shows/<tid>')
def show(tid):
  query = "SELECT tid, name, description FROM shows where tid = '{0}'".format(tid)
  cursor = g.conn.execute(query)
  show = cursor.first()
  cursor.close()  

  # get seasons
  query = "SELECT sid, release_date, number FROM seasons where tid = '{0}'".format(tid)
  cursor = g.conn.execute(query)
  seasons = []

  for result in cursor:
    seasons.append(result)
  cursor.close()

  return render_template("show.html", show=show, seasons=seasons)

@app.route('/shows/<tid>/seasons/<sid>')
def season(tid,sid):
  query = "SELECT sid, release_date, number FROM seasons where tid = '{0}'".format(tid)
  cursor = g.conn.execute(query)
  season = cursor.first()
  cursor.close()  

  # get episodes
  query = "SELECT eid, title, duration, release_date, sid number FROM episodes where sid = '{0}'".format(sid)
  cursor = g.conn.execute(query)
  episodes = []

  for result in cursor:
    episodes.append(result)
  cursor.close()

  return render_template("season.html", season=season, episodes=episodes)

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug=True)
