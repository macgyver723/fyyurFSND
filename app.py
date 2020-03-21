#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from datetime import datetime
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import enum
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Venue(db.Model):
  __tablename__ = 'venues'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), nullable=False)
  city = db.Column(db.String(120), nullable=False)
  state = db.Column(db.String(120), nullable=False)
  address = db.Column(db.String(120), nullable=False)
  phone = db.Column(db.String(120), nullable=False)
  genres = db.Column(db.String(), nullable=False) # csv 
  image_link = db.Column(db.String(500), nullable=False)
  facebook_link = db.Column(db.String(120), nullable=False)
  website = db.Column(db.String(120), nullable=False)
  seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
  seeking_description = db.Column(db.String(), nullable=False, default="Not currently seeking talent")
  shows = db.relationship('Show', backref='venue', lazy=True)

  def getVenueDict(self):
    num_upcoming_shows = len(self.getShows('upcoming'))
    return {
      "id" : self.id,
      "name" : self.name,
      "num_upcoming_shows" : num_upcoming_shows,
    }

  def getShows(self, when):
    if when == 'upcoming':
      query = Show.query.filter(Show.venue_id == self.id).filter(Show.start_time > datetime.now()).order_by(Show.start_time).all()
    elif when == 'past':
      query = Show.query.filter(Show.venue_id == self.id).filter(Show.start_time < datetime.now()).order_by(Show.start_time).all()
    else:
      print("unexpected value for variable <when>")
      return []
    
    shows = []
    for q in query:
      this_show = {}
      this_show['artist_id'] = q.artist_id
      this_show['artist_name'] = Artist.query.filter_by(id=q.artist_id).first().name
      this_show['artist_image_link'] = Artist.query.filter_by(id=q.artist_id).first().image_link
      this_show['start_time'] = str(q.start_time)
      shows.append(this_show)
    return shows
  
  def getGenresList(self):
    return self.genres.split(",")
  
  def __repr__(self):
    return f"<Venue {self.id} {self.name} {self.city}, {self.state}>"

class Artist(db.Model):
  __tablename__ = 'artists'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), nullable=False)
  city = db.Column(db.String(120), nullable=False)
  state = db.Column(db.String(120), nullable=False)
  phone = db.Column(db.String(120), nullable=False)
  genres = db.Column(db.String(), nullable=False) # csv
  image_link = db.Column(db.String(500), nullable=False)
  facebook_link = db.Column(db.String(120), nullable=False)
  website = db.Column(db.String(120), nullable=True)
  seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
  seeking_description = db.Column(db.String(), nullable=False, default="Not currently seeking performance venues")
  shows = db.relationship('Show', backref='artist', lazy=True)

  def getShows(self, when):
    '''
    return list of either upcoming or past shows for this artist
    @param when "upcoming" or "past"
    @return list of shows as dicts
    '''
    if when == 'upcoming':
      query = Show.query.filter(Show.artist_id == self.id).filter(Show.start_time > datetime.now()).order_by(Show.start_time).all()
    elif when == 'past':
      query = Show.query.filter(Show.artist_id == self.id).filter(Show.start_time < datetime.now()).order_by(Show.start_time).all()
    else:
      print("unexpected value for variable <when>")
      return []
    
    shows = []
    for q in query:
      this_show = {}
      this_show['venue_id'] = q.venue_id
      this_show['venue_name'] = Venue.query.filter_by(id=q.venue_id).first().name
      this_show['venue_image_link'] = Venue.query.filter_by(id=q.venue_id).first().image_link
      this_show['start_time'] = str(q.start_time)
      shows.append(this_show)
    return shows
    
  def __repr__(self):
    return f"<Artist {self.id} {self.name} {self.city}, {self.state}>"

class Show(db.Model):
  __tablename__ = 'shows'
  id = db.Column(db.Integer, primary_key=True)
  start_time = db.Column(db.DateTime(), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)



#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data = []
  venues_sorted = Venue.query.order_by(Venue.state, Venue.city).all()
  this_city_dict = {}
  for v in venues_sorted:
    if 'city' not in this_city_dict: # first time through the loop, nothing in this_city_dict
      this_city_dict['city'] = v.city
      this_city_dict['state'] = v.state
      this_city_dict['venues'] = []
    elif (this_city_dict['city'] != v.city and this_city_dict['state'] != v.state): # new city/state
      data.append(this_city_dict) # add this_city_dict to the data list
      this_city_dict = {}
      this_city_dict['city'] = v.city
      this_city_dict['state'] = v.state
      this_city_dict['venues'] = []
      
    this_city_dict['venues'].append(v.getVenueDict()) # add this venue to the venue list in this_city_dict
  # add last this_city_dict to data list
  data.append(this_city_dict)

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term','')
  query = Venue.query.filter(Venue.name.ilike('%'+search_term.lower()+'%')).all()
  data = [{
    'id' : q.id,
    'name' : q.name,
    'num_upcoming_shows' : q.getShows("upcoming")
    } for q in query]
  response={
    "count": len(query),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id

  venue = Venue.query.filter_by(id=venue_id).first()
  data = vars(venue)
  data['genres'] = data['genres'].split(',')
  data['past_shows'] = venue.getShows('past')
  data['upcoming_shows'] = venue.getShows('upcoming')
  data['past_shows_count'] = len(data['past_shows'])
  data['upcoming_shows_count'] = len(data['upcoming_shows'])

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm()
  success = False
  try:
    venue = Venue(
      name=form.name.data,
      city=form.city.data,
      state=form.state.data,
      phone=form.phone.data,
      address=form.address.data,
      image_link=form.image_link.data,
      facebook_link=form.facebook_link.data,
      genres=",".join(form.genres.data),
      seeking_talent=form.seeking_talent.data,
      seeking_description=form.seeking_description.data,
      website=form.website.data
    )
    db.session.add(venue)
    db.session.commit()
    success = True
  except Exception as e:
    success = False
    db.session.rollback()
    print(e)
  finally:
    db.session.close()

  if success:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  else:
    flash(f'An error occured. Venue {form.name.data} could not be listed.')
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    venue = Venue.query.filter_by(id=venue_id).first()
    shows = Show.query.filter(Show.venue_id == venue_id).all()
    name = venue.name
    [db.session.delete(s) for s in shows]
    db.session.delete(venue)
    db.session.commit()
  except Exception as e:
    print(f"exception {e} in delete_venue()")
  finally:
    db.session.close()

  flash(f'deleted Venue: {name}')
  return jsonify(url=url_for('index'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():  
  artists = Artist.query.order_by(Artist.name).all()
  data = [{
    'id' : a.id,
    'name' : a.name,
  } for a in artists]

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term','')
  query = Artist.query.filter(Artist.name.ilike('%'+search_term.lower()+'%')).all()
  data = [{
    'id' : q.id,
    'name' : q.name,
    'num_upcoming_shows' : q.getShows("upcoming")
    } for q in query]
  response={
    "count": len(query),
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id

  artist = Artist.query.filter_by(id=artist_id).first()
  data = vars(artist)
  data['genres'] = data['genres'].split(',')
  data['past_shows'] = artist.getShows('past')
  data['upcoming_shows'] = artist.getShows('upcoming')
  data['past_shows_count'] = len(data['past_shows'])
  data['upcoming_shows_count'] = len(data['upcoming_shows'])
  
  return render_template('pages/show_artist.html', artist=data)

@app.route('/artists/<int:artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
  try:
    artist = Artist.query.filter_by(id=artist_id).first()
    name = artist.name
    shows = Show.query.filter(Show.artist_id == artist_id).all()
    [db.session.delete(s) for s in shows]
    db.session.delete(artist)
    db.session.commit()
  except Exception as e:
    print(f"exceptions {e} in delete_artist()")
  finally:
    db.session.close()
  
  flash(f"Deleted Artist: {name}")

  return jsonify(url=url_for('index'))

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.filter_by(id=artist_id).first()
  form = ArtistForm(state=artist.state, genres=artist.genres.split(','))
  
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm()
  try:
    artist = Artist.query.filter_by(id=artist_id).first()
    artist.name = form.name.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.genres = ','.join(form.genres.data)
    artist.image_link = form.image_link.data
    artist.website = form.website.data
    artist.seeking_venue = form.seeking_venue.data
    artist.seeking_description = form.seeking_description.data
    artist.facebook_link = form.facebook_link.data
    db.session.commit()
  except Exception as e:
    print(f'Exception {e} in edit_artist_submission')
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.filter_by(id=venue_id).first()
  form = VenueForm(state=venue.state, genres=venue.genres.split(','))

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm()
  try:
    venue = Venue.query.filter_by(id=venue_id).first()
    venue.name = form.name.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.address = form.address.data
    venue.phone = form.phone.data
    venue.genres = ",".join(form.genres.data)
    venue.image_link = form.image_link.data
    venue.facebook_link = form.facebook_link.data
    venue.website = form.website.data
    venue.seeking_talent = form.seeking_talent.data
    venue.seeking_description = form.seeking_talent.data
    db.session.commit()
  except Exception as e:
    print(f"Exception {e} in edit_venue_submission")
  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  form = ArtistForm()
  success = False
  try:
    artist = Artist(
      name=form.name.data,
      city=form.city.data,
      state=form.state.data,
      phone=form.phone.data,
      image_link=form.image_link.data,
      facebook_link=form.facebook_link.data,
      genres=",".join(form.genres.data),
      seeking_venue=form.seeking_venue.data,
      seeking_description=form.seeking_description.data,
      website=form.website.data
    )
    db.session.add(artist)
    db.session.commit()
    success = True
  except:
    success = False
    db.session.rollback()
  finally:
    db.session.close()

  if success:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  else:
    flash(f'An error occured. Arist {form.name.data} could not be listed.')
  
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows

  data = [{
    'venue_id' : s.venue_id,
    'venue_name' : Venue.query.filter(Venue.id == s.venue_id).first().name,
    'artist_id' : s.artist_id,
    'artist_name' : Artist.query.filter(Artist.id == s.artist_id).first().name,
    'artist_image_link' : Artist.query.filter(Artist.id == s.artist_id).first().image_link,
    'start_time' : str(s.start_time)
  } for s in Show.query.order_by(Show.start_time.desc()).all()]

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  form = ShowForm()
  success = False
  try:
    show = Show(
      artist_id=form.artist_id.data,
      venue_id=form.venue_id.data,
      start_time=form.start_time.data
    )
    db.session.add(show)
    db.session.commit()
    success = True
  except Execption as e:
    print(e)
    success = False
    db.session.rollback()
  finally:
    db.session.close()
  
  if success:
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  else:
    flash('An error occurred. Show could not be listed.')
  
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''


