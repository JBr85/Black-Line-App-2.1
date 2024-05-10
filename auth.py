from flask import Blueprint, render_template

auth = Blueprint('auth', __name__)

@auth.route('/signon')
def signon():
    return render_template("signon.html")

@auth.route('/qualifying')
def qualifying():
    return render_template("qualifying.html")

@auth.route('/round1')
def round_1():
    return render_template("round_1.html")

@auth.route('/rep-1')
def rep_1():
    return render_template("rep1.html")

@auth.route('/round2')
def round_2():
    return render_template("round_2.html")

@auth.route('/minor-final-1')
def minorfinals1():
    return render_template("minorfinals1.html")

@auth.route('/semifinal')
def semifinal():
    return render_template("semifinal.html")

@auth.route('/minor-finals-2')
def minorfinals2():
    return render_template("minorfinals2.html")

@auth.route('/finals')
def finals():
    return render_template("finals.html")

@auth.route('/live')
def live():
    return render_template("Live.html")

@auth.route('/table')
def table():
    return render_template("table.html")

@auth.route('/upload')
def table():
    return render_template("upload.html")