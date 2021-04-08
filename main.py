import datetime
from random import choice as chs
from flask_wtf import FlaskForm
from sqlalchemy import or_
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField
from wtforms.fields.html5 import EmailField
from werkzeug.security import generate_password_hash
from wtforms.validators import DataRequired, EqualTo, Email
from flask import Flask, render_template, redirect, request
from data import db_session
from flask_login import LoginManager, login_required, logout_user
from flask_login import login_user, current_user
from data.dialog import Dialog
from data.forms import RegisterForm, FinishRegistration, LoginForm, DialogForm, SearchFriendForm
from data.users import User
from post_service.post_srv import send_mail

app = Flask(__name__)
app.config["SECRET_KEY"] = "super_secret_key_QWav43sd-svs3-001a"
login_manager = LoginManager()
login_manager.init_app(app)
MESSAGE_SPECIAL_SYMBOL_0 = "&&#/*/*/#&&"
MESSAGE_SPECIAL_SYMBOL_1 = "&~&end*mes&~&"
DIALOGS_DIR = "db/dialogs/"


# функция запуска приложения
def main():
    db_session.global_init("db/hestia_main.db")
    app.run()


# функция генерирующая код для завершения регистрации
def generate_code():
    code = str(chs(range(10)))\
           + str(chs(range(10)))\
           + str(chs(range(10)))\
           + str(chs(range(10)))\
           + str(chs(range(10)))\
           + str(chs(range(10)))
    return code


CODE = generate_code()


# функция получения последнего сообщения из диалога
def get_last_message(dlg: Dialog):
    mes = ""
    try:
        with open(f"{DIALOGS_DIR}{dlg.file}", "r") as f:
            al = f.read().split(MESSAGE_SPECIAL_SYMBOL_1)
            print(al)
            mes = al[-2].split(MESSAGE_SPECIAL_SYMBOL_0)[1]
            if len(mes) > 50:
                mes = mes[:51]
    except Exception:
        pass
    return mes


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


# функция c декоратором для регистрации пользователя
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


# функция c декоратором для завершения регистрации
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
                CODE = generate_code()
                return redirect("/")
            else:
                alert = "Uncorrect code"
            CODE = generate_code()
    else:
        alert = "Что то не так"
    return render_template("finish.html", form=form, title="Finish Registration", alert=alert)


# главная страница социальной сети
@app.route("/")
def base():
    return render_template("base.html", title="Hestia")


# главная страница пользователя социальной сети
@app.route("/<shortname>")
def logined(shortname):
    return render_template("base.html", title="My profile")


# функция с декоратором для входа в аккаунт
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.shortname == form.shortname.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(f"/{user.shortname}")
        return render_template('login.html',
                               message="Incorrect login or password",
                               form=form)
    return render_template('login.html', title='Authorization', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


# функция для открытия диалогов пользователя на сайте
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
        last_message = get_last_message(d)
        print(last_message)
        dialog_objects.append({"member": mem_obj.name + " " + mem_obj.surname,
                               "id": d.id,
                               "updated": d.modified_date,
                               "last_message": last_message})
    return render_template("messages.html", dialogs=dialog_objects, title="Messages")


# функция открытия конкретного диалога
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
    shortname = user.shortname
    dlg_file = q.file
    if request.method == "POST":
        if form.validate_on_submit():
            with open(f"{DIALOGS_DIR}{dlg_file}", "a+", encoding="utf-8") as dlg:
                dlg.write(f"{current_user.id}{MESSAGE_SPECIAL_SYMBOL_0}{form.input_line.data}{MESSAGE_SPECIAL_SYMBOL_1}")
            form.input_line.data = ""
            q.modified_date = datetime.datetime.now()
    with open(f"{DIALOGS_DIR}{dlg_file}", "r", encoding="utf-8") as dlg:
        m = dlg.read().split(MESSAGE_SPECIAL_SYMBOL_1)
        try:
            for num, i in enumerate(m):
                text = i.split(MESSAGE_SPECIAL_SYMBOL_0)[1]
                user = int(i.split(MESSAGE_SPECIAL_SYMBOL_0)[0])
                dlg_mes[num] = {"user": user, "text": text}
        except:
            pass
    return render_template("dialog.html", messages=dlg_mes,
                           member=member,
                           form=form,
                           title=f"Dialog with {member}",
                           shortname=shortname)


# функция открывающаяя страницу со списком друзей пользователя
@app.route("/friends")
@login_required
def friends():
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    friends = []
    try:
        print("hr")
        friends = user.friends.split(";")
        print(friends)
        friends = list(map(lambda x: [db_sess.query(User).filter(User.id == int(x)).first().name
                                     + " "
                                     + db_sess.query(User).filter(User.id == int(x)).first().surname,
                                      db_sess.query(User).filter(User.id == int(x)).first().shortname,
                                      db_sess.query(User).filter(User.id == int(x)).first().id], friends))
    except Exception:
        pass
    return render_template("friends.html", friends=friends, title="Friends")


# функция открывающаяя страницу с поиском новых друзей
@app.route("/friends/search", methods=["POST", "GET"])
@login_required
def search():
    db_sess = db_session.create_session()
    cu = db_sess.query(User).filter(User.id == current_user.id).first()
    form = SearchFriendForm()
    if form.validate_on_submit():
        searched_users = db_sess.query(User).filter(or_(User.shortname.like(f"%{form.input_line.data}%"),
                                                        User.name.like(f"%{form.input_line.data}%"),
                                                        User.surname.like(f"%{form.input_line.data}%"))).all()

        searched_users = list(map(lambda x: [x.name + " " + x.surname,
                                             x.shortname,
                                             x.id,
                                             1 if x.id != current_user.id
                                                      or (str(x.id) not in cu.friends
                                                          and str(x.id) not in cu.request) else 0],
                                  searched_users))
    else:
        searched_users = db_sess.query(User).filter().all()
        searched_users = list(map(lambda x: [x.name + " " + x.surname, x.shortname, x.id], searched_users))
    return render_template("search_friends.html", title="Searching Friends", searched_users=searched_users, form=form)


# функция создающаяя диалог с пользователем
@app.route("/new_dialog/<int:member_id>")
@login_required
def new_dialog(member_id):
    db_sess = db_session.create_session()
    q = db_sess.query(Dialog).filter(or_(Dialog.members == f"{current_user.id};{member_id}",
                                         Dialog.members == f"{member_id};{current_user.id}")).first()
    if q:
        return redirect(f"/dialog/{q.id}")
    else:
        dlg = Dialog()
        dlg.members = f"{current_user.id};{member_id}"
        dlg.file = ""
        db_sess.add(dlg)
        db_sess.commit()
        dlg.file = f"dialog{dlg.id}.dlg"
        db_sess.commit()
        f = open(f"{DIALOGS_DIR}{dlg.file}", "w", encoding="utf-8")
        f.close()
        return redirect(f"/dialog/{dlg.id}")


# функция открывающаяя страницу с запросами в друзья
@app.route("/friends/requests", methods=["GET", "POST"])
@login_required
def requests():
    db_sess = db_session.create_session()
    message = ""
    req = []
    rq = list(filter(lambda x: x != " " and x != "", current_user.requests.split(";")))
    try:
        req = list(map(lambda x: db_sess.query(User).filter(User.id == int(x)).first(), rq))
    except Exception:
        message = "No requests"
    return render_template("requests.html", title="Friend requests", message=message, req=req)


# функция добавляющая друга
@app.route("/addfriend/<int:user_id>")
@login_required
def add_friend(user_id):
    req = current_user.requests.split(";")
    if str(user_id) in req:
        del req[req.index(str(user_id))]
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == user_id).first()
        if user.friends:
            user.friends = user.friends + f";{current_user.id}"
        else:
            user.friends = f"{current_user.id}"
        cu = db_sess.query(User).filter(User.id == current_user.id).first()
        if cu.friends:
            print("dada")
            cu.friends = cu.friends + f";{user_id}"
        else:
            cu.friends = f"{user_id}"
            db_sess.commit()
        cu.requests = ";".join(req)
        db_sess.commit()
    return redirect("/friends/requests")


# функция создающая запрос в друзья
@app.route("/friends/makerequest/<int:user_id>")
@login_required
def make_request(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    user.requests = user.requests + f";{current_user.id}"
    db_sess.commit()
    return redirect("/friends/search")


if __name__ == "__main__":
    main()