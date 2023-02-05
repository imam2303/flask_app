from array import array
import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from flask import Flask, render_template, request, redirect, jsonify, json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from dotenv import load_dotenv
import pickle
import os
from flask_serialize import FlaskSerialize
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import os

load_dotenv()

app = Flask(__name__)
model = pickle.load(open("model.pkl", "rb"))
CORS(app)



app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


fs_mixin = FlaskSerialize(db)

# Setup the Flask-JWT-Extended extension
app.config["JWT_SECRET_KEY"] = "super-secret"  # Change this!
jwt = JWTManager(app)

class DataPrediksi(fs_mixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(30), nullable=False)
    alamat = db.Column(db.String(50), nullable=False)
    jenis_pmks = db.Column(db.Integer, nullable=False)
    hubungan_dlm_keluarga = db.Column(db.Integer, nullable=False)
    jml_tanggungan_kepala_keluarga = db.Column(db.Integer, nullable=False)
    pendapatan_keluarga = db.Column(db.Integer, nullable=False)
    status_rumah = db.Column(db.Integer, nullable=False)
    pekerjaan = db.Column(db.Integer, nullable=False)
    layak_tidak = db.Column(db.String(10), nullable=False)


@app.route("/login", methods=["POST"])
def login():
    username = request.json.get("username", None)
    password = request.json.get("password", None)
    if username != "admin" or password != "admin":
        return jsonify({"msg": "Username dan Password Salah!"}), 401

    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token)

@app.route("/", methods=["GET"])
def home():
    db.create_all()     
    return render_template('landing.html')

@app.route("/rumah", methods=["GET"])
def rumah():  
    return render_template('index1.html')

@app.route("/dataset", methods=["GET"])
def dataset():
    SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
    json_url = os.path.join(SITE_ROOT, "", "dataset.json")
    data = json.load(open(json_url))
    return render_template('read.html', data=data)

@app.route("/predict", methods=["GET"])
def predict_home():
    return render_template('index.html')
    
@app.route("/item/<item_id>", methods=["GET"])
@app.route("/items")
@jwt_required()
def table(item_id = None):
   return DataPrediksi.fs_get_delete_put_post(item_id)


@app.route("/create-predict", methods=["POST"])
@jwt_required()
def predict():
    data = request.get_json()

    fitur = np.array([
        int(data["jenis_pmks"]),
        int(data["hubungan_dlm_keluarga"]),
        int(data["jml_tanggungan_kepala_keluarga"]),
        int(data["pendapatan_keluarga"]),
        int(data["status_rumah"]),
        int(data["pekerjaan"])
    ])

    numpyArray = [np.array(fitur)]

    bener = np.array(numpyArray)

    prediction = model.predict(bener)

    formated_predict = f"{prediction}".replace("[", "").replace("]", "").replace("'", "")

    populate_data = DataPrediksi(
        nama=data["nama"],
        alamat=data["alamat"],
        jenis_pmks=data["jenis_pmks"],
        hubungan_dlm_keluarga=data["hubungan_dlm_keluarga"],
        jml_tanggungan_kepala_keluarga=data["jml_tanggungan_kepala_keluarga"],
        pendapatan_keluarga=data["pendapatan_keluarga"],
        status_rumah=data["status_rumah"],
        pekerjaan=data["pekerjaan"],
        layak_tidak=formated_predict
    )

    db.session.add(populate_data)
    db.session.commit()

    return {
        "layak_tidak": formated_predict
    }

if __name__ == "__main__":
    app.run(debug=True)