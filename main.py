import datetime
from random import choice as chs
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField
from wtforms.fields.html5 import EmailField
from werkzeug.security import generate_password_hash
from wtforms.validators import DataRequired, EqualTo, Email
from flask import Flask, render_template, redirect, request
from data import db_session
from flask_login import LoginManager, login_required, logout_user
from flask_login import login_user, current_user
from data.forms import RegisterForm, FinishRegistration
from data.users import User
from post_service.post_srv import send_mail

app = Flask(__name__)
app.config["SECRET_KEY"] = "super_secret_key_QWav43sd-svs3-001a"
login_manager = LoginManager()
login_manager.init_app(app)


def main():
    db_session.global_init("db/hestia_main.db")
    app.run()


def generate_code():
    code = str(chs(range(10)))\
           + str(chs(range(10)))\
           + str(chs(range(10)))\
           + str(chs(range(10)))\
           + str(chs(range(10)))\
           + str(chs(range(10)))
    return code


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/registration", methods=["POST", "GET"])
def register():
    form = RegisterForm()
    db_sess = db_session.create_session()
    if form.validate_on_submit():
        new_user = User()
        new_user.email = form.email.data
        new_user.address = form.address.data
        if form.shortname.data != "":
            new_user.shortname = form.shortname.data
        new_user.name = form.name.data
        new_user.surname = form.surname.data
        new_user.hashed_password = generate_password_hash(form.password.data)
        db_sess.add(new_user)
        db_sess.commit()
        return redirect(f"/finish/{new_user.id}")
    return render_template("register.html", form=form, title="Register")


@app.route("/finish/<int:u_id>", methods=["POST", "GET"])
def finish(u_id):
    code = generate_code()
    print(code)
    form = FinishRegistration()
    db_sess = db_session.create_session()
    usr = db_sess.query(User).filter(User.id == u_id)[0]
    email = usr.email
    alert = ""
    subject = "Завершение регистрации"
    text = f"Здравствуйте, {usr.name}.\n" \
           f"Вы заполниои форму регистрации Hestia.\n" \
           f"Для завершения регистрации введите код.\n" \
           f"Супер индивидуальный код: {code}"
    if send_mail(email, subject, text, []):
        if form.validate_on_submit():
            if code == str(form.code.data):
                usr.confirmed = True
                db_sess.commit()
                return redirect("/")
            else:
                alert = "Uncorrect code"
    else:
        alert = "Что то не так"
    return render_template("finish.html", form=form, title="Finish Registration", alert=alert)


@app.route("/")
def base():
    return render_template("base.html")


if __name__ == "__main__":
    main()