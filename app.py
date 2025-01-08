import os
from datetime import datetime, date

from flask import Flask, redirect, render_template, request, send_from_directory, url_for
from sqlalchemy import create_engine, MetaData, Table, ForeignKey, Column, String, Integer, Date, CHAR, CheckConstraint, join, DATETIME, func, text, select, PrimaryKeyConstraint, Identity, Sequence, case
from sqlalchemy.orm import sessionmaker, relationship, registry
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

# 2) Create your Flask Application
app = Flask(__name__, static_folder='static')
csrf = CSRFProtect(app)

# WEBSITE_HOSTNAME exists only in production environment
if 'WEBSITE_HOSTNAME' not in os.environ:
    # local development, where we'll use environment variables
    print("Loading config.development and environment variables from .env file.")
    app.config.from_object('azureproject.development')
else:
    # production
    print("Loading config.production.")
    app.config.from_object('azureproject.production')

# 3) Set the DATABASE URI
app.config.update(
    SQLALCHEMY_DATABASE_URI=app.config.get('DATABASE_URI'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

# 1) Initialize your DATABASE
db = SQLAlchemy(app)

# 4) Initialize a Flask App to use for the DATABASE
#db.init_app(app)

# Enable Flask-Migrate commands "flask db init/migrate/upgrade" to work
migrate = Migrate(app, db)

# The import must be done after db initialization due to circular import issue
from models import Bikes, Fahrten, Wartung, Wetter 


# Page content / Reports

# Table joins ( .select_from(<join>))
j_bf = join (Fahrten, Bikes, Bikes.bike == Fahrten.bike)
j_bw = join (Bikes, Wartung, Bikes.bike == Wartung.bike)
j_fw = join (Fahrten, Wetter, Fahrten.wetter == Wetter.bedingung)
j_wf = join(Fahrten, Wartung, Fahrten.bike == Wartung.bike and Fahrten.datum == Wartung.datum )

#old_wb=text("""select f.bike, case  when (select count (wartung_id) from wartung w2 where w2.bike = f.bike and w2.datum > (select max (w3.datum) from wartung w3 where w3.bike = f.bike and w3.service ='heiß')) = 0 then 0 else (select sum(f2.strecke) from fahrten f2 where f2.bike = f.bike and f2.datum >(select max(w2.datum) from wartung w2 where w2.bike = f.bike and w2.service ='kalt')) end as "Strecke seit kalt", (select sum(f3.strecke) from fahrten f3 where f3.bike = f.bike and f3.datum >(select max(w2.datum) from wartung w2 where w2.bike = f.bike and w2.service ='heiß')) as "Strecke seit heiß", case when (select count (wartung_id) from wartung w2 where w2.bike = f.bike and w2.datum > (select max (w3.datum) from wartung w3 where w3.bike = f.bike and w3.service ='heiß')) = 0 then 0  else (select sum(f4.strecke * w.faktor) from fahrten f4  join wetter w on f4.wetter = w.bedingung where f4.bike = f.bike and f4.datum >(select max(w2.datum) from wartung w2 where w2.bike = f.bike and w2.service ='kalt')) end as "Last seit kalt", (select sum(f5.strecke * w.faktor) from fahrten f5 join wetter w on f5.wetter = w.bedingung  where f5.bike = f.bike and f5.datum >(select max(w2.datum) from wartung w2 where w2.bike = f.bike and w2.service ='heiß')) as "Last seit heiß", (select count (wartung_id) from wartung w2 where w2.bike = f.bike and w2.service='kalt' and w2.datum > (select max (w3.datum) from wartung w3 where w3.bike = f.bike and w3.service ='heiß')) as "Wartungen kalt seit heiß", (select max(w2.datum) from wartung w2 where w2.bike = f.bike and w2.service ='kalt') as "Letzter Service kalt", (select max(w2.datum) from wartung w2 where w2.bike = f.bike and w2.service ='heiß') as "Letzter Service heiß" from fahrten f group by f.bike ;""")
#old_q_wb= db.session.execute(wb)

def wartungsbedarf():
    subquery_max_datum_heiss = select(func.max(Wartung.datum)).filter(Wartung.bike == Fahrten.bike, Wartung.service == 'heiß').scalar_subquery()
    subquery_max_datum_kalt = select(func.max(Wartung.datum)).filter(Wartung.bike == Fahrten.bike, Wartung.service == 'kalt').scalar_subquery()
    subquery_count_wartung_id_heiss = select(func.count(Wartung.wartung_id)).filter(Wartung.bike == Fahrten.bike, Wartung.datum > subquery_max_datum_heiss).scalar_subquery()
    subquery_sum_strecke_kalt = select(func.sum(Fahrten.strecke)).filter(Fahrten.bike == Fahrten.bike, Fahrten.datum > subquery_max_datum_kalt).scalar_subquery()
    subquery_sum_strecke_heiss = select(func.sum(Fahrten.strecke)).filter(Fahrten.bike == Fahrten.bike, Fahrten.datum > subquery_max_datum_heiss).scalar_subquery()
    subquery_sum_last_kalt = select(func.sum(Fahrten.strecke * Wetter.faktor)).join(Wetter, Fahrten.wetter == Wetter.bedingung).filter(Fahrten.bike == Fahrten.bike, Fahrten.datum > subquery_max_datum_kalt).scalar_subquery()
    subquery_sum_last_heiss = select(func.sum(Fahrten.strecke * Wetter.faktor)).join(Wetter, Fahrten.wetter == Wetter.bedingung).filter(Fahrten.bike == Fahrten.bike, Fahrten.datum > subquery_max_datum_heiss).scalar_subquery()
    subquery_count_wartung_id_kalt = select(func.count(Wartung.wartung_id)).filter(Wartung.bike == Fahrten.bike, Wartung.service == 'kalt', Wartung.datum > subquery_max_datum_heiss).scalar_subquery()
    subquery_max_datum_kalt_service = select(func.max(Wartung.datum)).filter(Wartung.bike == Fahrten.bike, Wartung.service == 'kalt').scalar_subquery()
    subquery_max_datum_heiss_service = select(func.max(Wartung.datum)).filter(Wartung.bike == Fahrten.bike, Wartung.service == 'heiß').scalar_subquery()
    # Define the main query
    q_wb = db.session.query(
    Fahrten.bike,
    case(
        [
            (subquery_count_wartung_id_heiss == 0, 0),
        ],
        else_=subquery_sum_strecke_kalt
    ).label("Strecke seit kalt"),
    subquery_sum_strecke_heiss.label("Strecke seit heiß"),
    case(
        [
            (subquery_count_wartung_id_heiss == 0, 0),
        ],
        else_=subquery_sum_last_kalt
    ).label("Last seit kalt"),
    subquery_sum_last_heiss.label("Last seit heiß"),
    subquery_count_wartung_id_kalt.label("Wartungen kalt seit heiß"),
    subquery_max_datum_kalt_service.label("Letzter Service kalt"),
    subquery_max_datum_heiss_service.label("Letzter Service heiß")
    ).group_by(Fahrten.bike)
    return q_wb

# Routes
@app.route("/")
def home():
    print('Request for home page received')
    return render_template("home.html")
# New functions
@app.route("/fahrten/", methods=['GET', 'POST'])
def fahrten():
    #if request.method =='POST':
     #   print('Request for add fahrt on fahrten received')
      #  lfndnr = request.form['lfndnr']
       # fahrt_to_delete = db.session.query(Fahrten).filter(Fahrten.fahrt_id == "lfndnr")
        #session.delete(fahrt_to_delete)
        #db.session.commit()
        #return redirect(f"/fahrten")
    #else:
     #   print('Request for fahrten page received')
    fahrten_headings = ("Laufende Nr.","Fahrrad", "Datum", "Strecke", "Wetter", "Strava ID")
    q_list_fahrten = db.session.query(Fahrten.fahrt_id, Fahrten.bike, Fahrten.datum, Fahrten.strecke, Fahrten.wetter, Fahrten.strava_id).order_by(Fahrten.datum.desc()).all()
    return render_template("fahrten.html", headings=fahrten_headings, data = q_list_fahrten)
@app.route("/neuefahrt/", methods=['GET', 'POST'])
def neuefahrt():
    print('Request for neue fahrt page received')
    if request.method =='POST':
        bike = request.form['bike']
        datum = request.form['datum']
        strecke = request.form['strecke']
        wetter = request.form['wetter']
        strava_id=request.form['strava_id']
        addfahrt = Fahrten(bike=bike, datum=datum, strecke=strecke, wetter=wetter, strava_id=strava_id)
        db.session.add(addfahrt)
        db.session.commit()
        flash('Fahrt erfolgreich hinzugefügt') # wird nicht angezeigt?
        return redirect(f"/fahrten/")
    else:
        return render_template("/neuefahrt.html/")
@app.route("/neuewartung/", methods=['GET', 'POST'])
def neuewartung(): 
    print('Request for neue wartung page received')
    if request.method =='POST':
        #wartung_id = request.form['wartung_id']
        bike = request.form['bike']
        datum = request.form['datum']
        service = request.form['service']
        notes = request.form['notes']
        addwartung = Wartung( bike=bike, datum=datum, service=service, notes=notes)
        db.session.add(addwartung) # und das hier auch
        db.session.commit()
        return redirect(f"/wartung/")
    else:
        return render_template("/neuewartung.html/")
@app.route("/wartung/")
def wartung():
    print('Request for wartung page received')
    wartung_headings = ("Laufende Nr.","Fahrrad", "Datum", "Service", "Notizen", "KM-Stand")
    q_wb_headings = ("Fahrrad", "Strecke seit kalt", "Strecke seit heiß", "Last seit kalt", "Last seit heiß","Wartungen kalt (seit heiß)", "Letzter Service kalt", "Letzter Service heiß")
    q_list_wartung = db.session.query(Wartung.wartung_id, Wartung.bike, Wartung.datum, Wartung.service, Wartung.notes, func.sum(Fahrten.strecke).filter(Fahrten.datum <= Wartung.datum)).select_from(j_wf).group_by(Wartung.wartung_id).order_by(Wartung.datum.desc()).all()
    return render_template("wartung.html", headings=q_wb_headings, data=wartungsbedarf(), headings_2=wartung_headings, data_2= q_list_wartung)
@app.route("/bikes/")
def bikes():
    print('Request for bikes page received')
    bike_headings = ("Fahrrad", "KM-Stand", "Letzte Fahrt")
    q_list_bikes = db.session.query(Bikes.bike, (Bikes.km_stand + func.sum(Fahrten.strecke)),func.max(Fahrten.datum)).select_from(j_bf).group_by(Bikes.bike).all()
    return render_template("bikes.html", headings=bike_headings, data=q_list_bikes)

if __name__ == '__main__':
    app.run()
