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
from data.dialog import Dialog
from data.forms import RegisterForm, FinishRegistration, LoginForm, DialogForm
from data.users import User
from post_service.post_srv import send_mail

app = Flask(__name__)
app.config["SECRET_KEY"] = "super_secret_key_QWav43sd-svs3-001a"
login_manager = LoginManager()
login_manager.init_app(app)
MESSAGE_SPECIAL_SYMBOL_0 = "&&#/*/*/#&&"
MESSAGE_SPECIAL_SYMBOL_1 = "&~&end*mes&~&"
DIALOGS_DIR = "dialogs/"


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


CODE = generate_code()


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
        if len(db_sess.query(User).filter(User.email == form.email.data).all()) != 0:
            return render_template("register.html", form=form, title="Register", message="This email already in use")
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
    global CODE
    print(CODE)
    form = FinishRegistration()
    db_sess = db_session.create_session()
    usr = db_sess.query(User).filter(User.id == u_id)[0]
    email = usr.email
    alert = ""
    subject = "Завершение регистрации"
    text = f"Здравствуйте, {usr.name}.\n" \
           f"Вы заполниои форму регистрации Hestia.\n" \
           f"Для завершения регистрации введите код.\n" \
           f"Супер индивидуальный код: {CODE}"
    if send_mail(email, subject, text, []):
        if form.validate_on_submit():
            print("code" + form.code.data)
            if CODE == str(form.code.data):
                usr.confirmed = True
                db_sess.commit()

                return redirect("/")
            else:
                alert = "Uncorrect code"
            CODE = generate_code()
    else:
        alert = "Что то не так"
    return render_template("finish.html", form=form, title="Finish Registration", alert=alert)


@app.route("/")
def base():
    return render_template("base.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.shortname == form.shortname.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Incorrect login or password",
                               form=form)
    return render_template('login.html', title='Authorization', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/messages")
@login_required
def messages():
    db_sess = db_session.create_session()
    dialogs = db_sess.query(Dialog).filter(Dialog.members.like(f"%{current_user.id}%")).all()
    dialog_objects = []
    for d in dialogs:
        member = int(d.members.split(";")[0])
        if member == current_user.id:
            member = int(d.members.split(";")[1])
        mem_obj = db_sess.query(User).filter(User.id == member).all()[0]
        dialog_objects.append({"member": mem_obj.name + mem_obj.surname, "id": d.id})
    return render_template("messages.html", dialogs=dialog_objects, title="Messages")


@app.route("/dialog/<dlg_id>", methods=["POST", "GET"])
@login_required
def dialog(dlg_id):
    form = DialogForm()
    dlg_mes = {}
    db_sess = db_session.create_session()
    q = db_sess.query(Dialog).filter(Dialog.id == dlg_id).first()
    member = int(q.members.split(";")[0])
    if member == current_user.id:
        member = int(q.members.split(";")[1])
    user = db_sess.query(User).filter(User.id == member).first()
    member = user.name + " " + user.surname
    dlg_file = q.file
    if request.method == "POST":
        if form.validate_on_submit():
            with open(f"{DIALOGS_DIR}{dlg_file}", "a+", encoding="utf-8") as dlg:
                dlg.write(f"{current_user.id}{MESSAGE_SPECIAL_SYMBOL_0}{form.input_line.data}{MESSAGE_SPECIAL_SYMBOL_1}")
            form.input_line.data = ""
    with open(f"{DIALOGS_DIR}{dlg_file}", "r", encoding="utf-8") as dlg:
        m = dlg.read().split(MESSAGE_SPECIAL_SYMBOL_1)
        try:
            for num, i in enumerate(m):
                text = i.split(MESSAGE_SPECIAL_SYMBOL_0)[1]
                user = int(i.split(MESSAGE_SPECIAL_SYMBOL_0)[0])
                dlg_mes[num] = {"user": user, "text": text}
        except:
            pass
    return render_template("dialog.html", messages=dlg_mes, member=member, form=form)


@app.route("/d")
def d():
    return render_template("d.html")


if __name__ == "__main__":
    main()