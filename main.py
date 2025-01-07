from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os


# FLASK APP CREATION
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
Bootstrap5(app)


# CREATE DB
class Base(DeclarativeBase):
    pass


# DB INITIALIZATION
db = SQLAlchemy(model_class= Base)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///my_watched.db"
db.init_app(app)


# CREATE TABLE
class Entry(db.Model):
    id: Mapped[int] = mapped_column(primary_key= True, nullable= False)
    type: Mapped[str] = mapped_column(nullable= False)
    title: Mapped[str] = mapped_column(unique= True, nullable= False)
    year: Mapped[int] = mapped_column(nullable= False)
    img_url: Mapped[str] = mapped_column(nullable= True)


with app.app_context():
    db.create_all()


# CREATE ADD FORM
class AddMovieForm(FlaskForm):
    name = StringField("Name", validators= [DataRequired()])
    submit = SubmitField("Add")


# new_entry = Entry(
#     type = "movie",
#     title = "Deadpool vs Wolverine",
#     year = 2024,
#     img_url = "https://m.media-amazon.com/images/M/MV5BNzRiMjg0MzUtNTQ1Mi00Y2Q5LWEwM2MtMzUwZDU5NmVjN2NkXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"
# )


# with app.app_context():
#     db.session.add(new_entry)
#     db.session.commit()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/list", methods=["GET", "POST"])
def list():
    entry_type = request.args.get("type")

    entries_list = db.session.execute(db.select(Entry).where(Entry.type == entry_type)).scalars().all()

    return render_template("list.html", list = entries_list)


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddMovieForm()

    type = request.args.get("type")

    if form.validate_on_submit():
        
        keyword = form.name.data

        params = {
                    "query": keyword
                }

        headers = {
                    "accept": "application/json",
                    "Authorization": os.environ.get("Bearer")
                }

        if type == "movie":
            api_url = "https://api.themoviedb.org/3/search/movie"

            result = requests.get(api_url, params= params, headers= headers).json()["results"]

            return render_template("select.html", list = result, type = type)
        
        elif type == "serie":

            api_url = "https://api.themoviedb.org/3/search/tv"

            result = requests.get(api_url, params= params, headers= headers).json()["results"]

            return render_template("select.html", list = result, type = type)

    return render_template("add.html", form = form)


@app.route("/select", methods = ["GET", "POST"])
def select():

    type = request.args.get("type")
    id = request.args.get("id")

    headers = {
                    "accept": "application/json",
                    "Authorization": os.environ.get("Bearer")
            }
    
    if type == "movie":

        url = f"https://api.themoviedb.org/3/movie/{id}"

        details = requests.get(url, headers = headers).json()
        print(details)

        new_entry = Entry(
            type = type,
            title = details["title"],
            year = details["release_date"].split("-")[0],
            img_url = f"https://image.tmdb.org/t/p/w500{details['poster_path']}"
        )

        db.session.add(new_entry)
        db.session.commit()

    else:

        url = f"https://api.themoviedb.org/3/tv/{id}"
        
        details = requests.get(url, headers = headers).json()
        print(details)

        new_entry = Entry(
            type = type,
            title = details["name"],
            year = details["first_air_date"].split("-")[0],
            img_url = f"https://image.tmdb.org/t/p/w500{details['poster_path']}"
        )

        db.session.add(new_entry)
        db.session.commit()

    

    return redirect(url_for("home"))


@app.route("/delete", methods=["GET", "POST"])
def delete():

    id = request.args.get("id")
    id_to_delete = db.get_or_404(Entry, id)

    db.session.delete(id_to_delete)
    db.session.commit()

    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True, port= 5001)