import datetime
import os
from random import choice as chs
from sqlalchemy import or_
from werkzeug.security import generate_password_hash
from flask import Flask, render_template, redirect, request
from data import db_session, user_resource, dialog_resource, news_resource
from flask_login import LoginManager, login_required, logout_user
from flask_login import login_user, current_user
from data.dialog import Dialog
from data.forms import RegisterForm, FinishRegistration, generate_code, CreateChatForm
from data.forms import LoginForm, DialogForm, EditForm, NewsForm
from data.forms import SearchFriendForm, FirstRecPswForm
from data.forms import SecondRecPswForm, ThirdRecPswForm, ChangePswForm
from data.users import User
from data.news import News
from post_service.post_srv import send_mail
from flask_restful import reqparse, abort, Api, Resource

MESSAGE_SPECIAL_SYMBOL_0 = "&#&/<-sndr/*/msg->/&#&"  # символ разделения отправителя от текста сообщения
MESSAGE_SPECIAL_SYMBOL_1 = "&~&/end/*/mes/&~&"  # символ разделения сообщений
DIALOGS_DIR = "db/dialogs/"  # расположение диалогов
CODE = generate_code()  # заранее генерируем код( при использовании он меняется )

# Инициализация приложения
app = Flask(__name__)
app.config["SECRET_KEY"] = "super_secret_key_QWav-43sd-svs3-001a"
app.config["UPLOAD_FOLDER"] = "static/user_images/"
login_manager = LoginManager()
login_manager.init_app(app)

# API приложения
api = Api(app)
api.add_resource(user_resource.UsersListResource, "/api/users")
api.add_resource(user_resource.UsersResource, "/api/users/<int:user_id>")
api.add_resource(dialog_resource.DialogsListResource, "/api/dialogs")
api.add_resource(dialog_resource.DialogsResource, "/api/dialogs/<int:dialog_id>")
api.add_resource(news_resource.NewsListResource, "/api/news")
api.add_resource(news_resource.NewsResource, "/api/news/<int:news_id>")


# функция запуска приложения
def main():
    db_session.global_init("db/hestia_main.db")
    app.run()


# функция получения последнего сообщения из диалога
def get_last_message(dlg: Dialog):
    mes = ""
    try:
        with open(f"{DIALOGS_DIR}{dlg.file}", "r", encoding="utf-8") as f:
            al = f.read().split(MESSAGE_SPECIAL_SYMBOL_1)
            mes = al[-2].split(MESSAGE_SPECIAL_SYMBOL_0)[1]
            if len(mes) > 50:
                mes = mes[:51]
    except Exception:
        pass
    return mes


# функция проверки принадлежности пользователя к списку друзей или списку запросов
def check_requests_friend(user):
    if str(current_user.id) in user.requests:
        return -1
    elif str(current_user.id) in user.friends or str(user.id) in current_user.requests:
        return 0
    else:
        return 1


# функция обновляющаяя время последнего действия пользователя
def update_time():
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    user.last_seen = datetime.datetime.now()
    db_sess.commit()


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
            return render_template("register.html",
                                   form=form,
                                   title="Register",
                                   message="This email already in use. Please, choice other.")
        elif len(db_sess.query(User).filter(User.shortname == form.shortname.data).all()) != 0:
            return render_template("register.html",
                                   form=form,
                                   title="Register",
                                   message="This shortname already in use. Please, choice other.")
        new_user.email = form.email.data
        new_user.address = form.address.data
        if form.shortname.data != "":
            new_user.shortname = form.shortname.data
        new_user.name = form.name.data
        new_user.surname = form.surname.data
        new_user.hashed_password = generate_password_hash(form.password.data)
        db_sess.add(new_user)
        db_sess.commit()
        os.mkdir(app.config['UPLOAD_FOLDER'] + new_user.shortname)
        return redirect(f"/finish/{new_user.id}")
    return render_template("register.html", form=form, title="Register")


# функция c декоратором для завершения регистрации
@app.route("/finish/<int:u_id>", methods=["POST", "GET"])
def finish(u_id):
    global CODE
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
    if request.method == "GET":
        sent = send_mail(email, subject, text, [])
        if not sent:
            sent = send_mail(email, subject, text, [])
            if not sent:
                alert = "Something is wrong, please try later."
    elif request.method == "POST":
        if form.validate_on_submit():
            if CODE == str(form.code.data):
                usr.confirmed = True
                db_sess.commit()
                CODE = generate_code()
                return redirect("/success/2")
            else:
                alert = "Incorrect code. Try again"
    return render_template("finish.html",
                           form=form,
                           title="Finish Registration",
                           alert=alert)


# главная страница социальной сети
@app.route("/")
def base():
    return render_template("welcome.html", title="Hestia")


# главная страница пользователя социальной сети
@app.route("/home/<shortname>")
def logined(shortname):
    return render_template("base.html", title="My profile")


# функция с декоратором для входа в аккаунт
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.shortname == form.shortname.data).first()
        if user is None:
            return render_template('login.html',
                                   message="Incorrect login or password",
                                   form=form, title='Authorization')
        if user and user.check_password(form.password.data) and user.confirmed:
            login_user(user, remember=form.remember_me.data)
            update_time()
            return redirect(f"/home/{user.shortname}")
        elif not user.confirmed:
            return redirect(f"/finish/{user.id}")
        return render_template('login.html',
                               message="Incorrect login or password",
                               form=form, title='Authorization')
    return render_template('login.html', title='Authorization', form=form)


@app.route("/logout")
@login_required
def logout():
    update_time()
    logout_user()
    return redirect("/")


# функция для открытия диалогов пользователя на сайте
@app.route("/messages")
@login_required
def messages():
    try:
        avatar = f""
        db_sess = db_session.create_session()
        update_time()
        dialogs = db_sess.query(Dialog).filter(or_(Dialog.members.like(f"%;{current_user.id}"),
                                                   Dialog.members.like(f"%;{current_user.id};%"),
                                                   Dialog.members.like(f"{current_user.id};%"),
                                                   Dialog.members == f"{current_user.id}")).all()
        dialog_objects = []
        for dialog in dialogs:
            if dialog.label != "_":
                label = dialog.label
            else:
                member = int(dialog.members.split(";")[0])
                if member == current_user.id:
                    member = int(dialog.members.split(";")[1])
                mem_obj = db_sess.query(User).filter(User.id == member).all()[0]
                if mem_obj.avatar is not None:
                    avatar = f"/static/user_images/{mem_obj.shortname}/{mem_obj.avatar}"
                else:
                    avatar = f"/static/user_images/anonym.jpg"
                label = mem_obj.name + " " + mem_obj.surname
            last_message = get_last_message(dialog)

            dialog_objects.append({"member": label,
                                   "id": dialog.id,
                                   "updated": dialog.modified_date,
                                   "last_message": last_message,
                                   "members_cnt": len(dialog.members.split(";"))
                                   })

            dialog_objects.sort(key=lambda x: str(x["last_message"]), reverse=False)
        return render_template("messages.html",
                               dialogs=dialog_objects,
                               title="Messages",
                               avatar=avatar)
    except Exception as e:
        print(e)
        return redirect("/")


# функция открытия конкретного диалога
@app.route("/dialog/<dlg_id>", methods=["POST", "GET"])
@login_required
def dialog(dlg_id):
    try:
        update_time()
        form = DialogForm()
        dlg_mes = {}
        db_sess = db_session.create_session()
        dialog = db_sess.query(Dialog).filter(Dialog.id == dlg_id).first()
        if dialog.label == "_":
            member = int(dialog.members.split(";")[0])
            if member == current_user.id:
                member = int(dialog.members.split(";")[1])
            user = db_sess.query(User).filter(User.id == member).first()
            if user.avatar is not None:
                avatar = f"/static/user_images/{user.shortname}/{user.avatar}"
            else:
                avatar = f"/static/user_images/anonym.jpg"
            member = user.name + " " + user.surname
            title = f"Dialog with {member}"
            last_seen = f"last action at {str(user.last_seen)[:-10]}"
        else:
            title = f"Chat {dialog.label}"
            member = dialog.label
            avatar = ""
            last_seen = ""
        dlg_file = dialog.file
        if request.method == "POST":
            if form.validate_on_submit():
                with open(f"{DIALOGS_DIR}{dlg_file}", "a+", encoding="utf-8") as dlg:
                    dlg.write(f"{current_user.id}{MESSAGE_SPECIAL_SYMBOL_0}"
                              f"{form.input_line.data}{MESSAGE_SPECIAL_SYMBOL_1}")
                form.input_line.data = ""
                dialog.modified_date = datetime.datetime.now()
                db_sess.commit()
        with open(f"{DIALOGS_DIR}{dlg_file}", "r", encoding="utf-8") as dlg:
            m = dlg.read().split(MESSAGE_SPECIAL_SYMBOL_1)
            try:
                for num, i in enumerate(m):
                    text = i.split(MESSAGE_SPECIAL_SYMBOL_0)[1]
                    user = int(i.split(MESSAGE_SPECIAL_SYMBOL_0)[0])
                    usr = db_sess.query(User).filter(User.id == user).first()
                    if usr.avatar is None:
                        member_avatar = f"/static/user_images/anonym.jpg"
                    else:
                        member_avatar = f"/static/user_images/{usr.shortname}/{usr.avatar}"
                    dlg_mes[num] = {"user": user,
                                    "text": text,
                                    "avatar": member_avatar,
                                    "name": usr.name}
            except:
                pass
        return render_template("dialog.html", messages=dlg_mes,
                               member=member,
                               form=form,
                               title=title,
                               last_seen=last_seen,
                               avatar=avatar)
    except Exception as e:
        print(e)
        return redirect("/messages")


# функция открывающаяя страницу со списком друзей пользователя
@app.route("/friends")
@login_required
def friends():
    try:
        update_time()
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        friends = []
        try:
            friends = user.friends.split(";")
            friends = list(filter(lambda x: x != "", friends))
            friends = list(map(lambda x:
                               [db_sess.query(User).filter(User.id == int(x)).first().name
                                + " "
                                + db_sess.query(User).filter(User.id == int(x)).first().surname,
                                db_sess.query(User).filter(User.id == int(x)).first().shortname,
                                db_sess.query(User).filter(User.id == int(x)).first().id,
                                db_sess.query(User).filter(User.id == int(x)).first().avatar],
                               friends))
        except Exception:
            pass
        return render_template("friends.html", friends=friends, title="Friends")
    except Exception:
        return redirect("/")


# функция открывающаяя страницу с поиском новых друзей
@app.route("/friends/search", methods=["POST", "GET"])
@login_required
def search():
    try:
        update_time()
        db_sess = db_session.create_session()
        cu = db_sess.query(User).filter(User.id == current_user.id).first()
        form = SearchFriendForm()
        in_ln = form.input_line.data
        if form.validate_on_submit():
            searched_users = db_sess.query(User).filter(
                or_(User.shortname.like(f"%"
                                        f"{in_ln}"
                                        f"%"),
                    User.name.like(f"%{form.input_line.data}%"),
                    User.surname.like(f"%{form.input_line.data}"
                                      f"%"))).all()

            searched_users = list(map(lambda x: [x.name + " " + x.surname,
                                                 x.shortname,
                                                 x.id,
                                                 check_requests_friend(x),
                                                 x.avatar],
                                      searched_users))
        else:
            searched_users = db_sess.query(User).filter().all()
            searched_users = list(map(lambda x: [x.name + " " + x.surname,
                                                 x.shortname,
                                                 x.id,
                                                 check_requests_friend(x),
                                                 x.avatar],
                                      searched_users))
        return render_template("search_friends.html",
                               title="Searching Friends",
                               searched_users=searched_users,
                               form=form)
    except Exception as e:
        print(e)
        return redirect("/friends")


# функция открывающая список друзей для приглашения в беседу
@app.route("/messages/invite/<dialog_id>", methods=["POST", "GET"])
@login_required
def invite_in_dialog(dialog_id):
    update_time()
    db_sess = db_session.create_session()
    dlg = db_sess.query(Dialog).filter(Dialog.id == dialog_id).first()
    dlg_members = list(filter(lambda x: x != "", dlg.members.split(";")))
    if len(dlg_members) == 2 and dlg.label == "":
        return redirect("/make_group_chat")
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    friends = []
    friends = user.friends.split(";")
    if request.method == "POST":
        for i in friends:
            try:
                if request.form[f"invite{i}"]:
                    dlg_members.append(i)
            except Exception as e:
                print(e)
        dlg.members = ";".join(dlg_members)
        db_sess.commit()
        return redirect("/messages")
    friends = list(filter(lambda x: x != "", friends))
    friends = list(map(lambda x: [db_sess.query(User).filter(User.id == int(x)).first().name
                                  + " "
                                  + db_sess.query(User).filter(User.id == int(x)).first().surname,
                                  db_sess.query(User).filter(User.id == int(x)).first().shortname,
                                  db_sess.query(User).filter(User.id == int(x)).first().id
                                  if str(db_sess.query(User).filter(User.id == int(x)).first().id)
                                     not in dlg_members
                                  else ""],
                       friends))
    return render_template("invite_friends.html", friends=friends, title="Invite")


# функция создающая групповой чат
@app.route("/messages/make_group_chat", methods=["POST", "GET"])
@login_required
def new_group_chat():
    db_sess = db_session.create_session()
    try:
        update_time()
        form = CreateChatForm()
        if form.validate_on_submit():
            dlg = Dialog()
            dlg.label = form.label.data
            dlg_id = max(list(map(lambda x: int(x.id),
                                  db_sess.query(Dialog).filter().all())) + [0]) + 1
            dlg.id = dlg_id
            dlg.file = f"dialog{dlg_id}.dlg"
            dlg.members = str(current_user.id)
            f = open(f"{DIALOGS_DIR}{dlg.file}", "w", encoding="utf-8")
            f.close()
            db_sess.add(dlg)
            db_sess.commit()
            return redirect(f"/messages/invite/{dlg_id}")
        return render_template("create_group_chat.html", form=form, title="Invite")
    except Exception:
        return redirect("/messages")


# функция создающаяя диалог с пользователем
@app.route("/messages/new_dialog/<int:member_id>", methods=["GET", "POST"])
@login_required
def new_dialog(member_id):
    try:
        update_time()
        db_sess = db_session.create_session()
        exist_dlg = db_sess.query(Dialog).filter(or_(
            Dialog.members == f"{current_user.id};{member_id}",
            Dialog.members == f"{member_id};{current_user.id}")).first()
        if exist_dlg:
            return redirect(f"/dialog/{exist_dlg.id}")
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
    except Exception:
        return redirect("/messages")


# функция удаляющая диалог
@app.route("/messages/delete_dialog/<int:dialog_id>", methods=["GET", "POST"])
@login_required
def delete_dialog(dialog_id):
    try:
        db_sess = db_session.create_session()
        dlg = db_sess.query(Dialog).filter(Dialog.id == dialog_id).first()
        members = ";".join(list(filter(lambda x: x != str(current_user.id), dlg.members.split(";"))))
        dlg.members = members
        db_sess.commit()
        return redirect(f"/messages")
    except Exception:
        return redirect("/messages")


# функция добавляющая участника в беседу
@app.route("/messages/add_member/<int:dialog_id>/<int:user_id>", methods=["GET", "POST"])
@login_required
def add_member(dialog_id, user_id):
    try:
        db_sess = db_session.create_session()
        dlg = db_sess.query(Dialog).filter(Dialog.id == dialog_id).first()
        dlg.members += ";" + str(user_id)
        db_sess.commit()
    except:
        pass
    return redirect("/messages")


# функция открывающая страницу с запросами в друзья
@app.route("/friends/requests", methods=["GET", "POST"])
@login_required
def requests():
    try:
        update_time()
        db_sess = db_session.create_session()
        message = ""
        req = []
        rq = list(filter(lambda x: x != " " and x != "", current_user.requests.split(";")))
        try:
            req = list(map(lambda x: db_sess.query(User).filter(User.id == int(x)).first(), rq))
        except Exception:
            message = "No requests"
        return render_template("requests.html",
                               title="Friend requests",
                               message=message,
                               req=req)
    except Exception:
        return redirect("/friends")


# функция добавляющая друга
@app.route("/addfriend/<int:user_id>")
@login_required
def add_friend(user_id):
    try:
        update_time()
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
                cu.friends = cu.friends + f";{user_id}"
            else:
                cu.friends = f"{user_id}"
                db_sess.commit()
            cu.requests = ";".join(req)
            db_sess.commit()
    except Exception:
        pass
    return redirect("/friends/requests")


# функция создающая запрос в друзья
@app.route("/friends/makerequest/<int:user_id>")
@login_required
def make_request(user_id):
    try:
        update_time()
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == user_id).first()
        req = user.requests.split(";")
        if str(current_user.id) not in user.requests:
            req.append(f"{current_user.id}")
        user.requests = ";".join(req)
        db_sess.commit()
        return redirect("/friends/search")
    except Exception:
        return redirect("/friends/search")


# функция удаления пользователя из списка друзей
@app.route("/friends/delete/<user_id>", methods=["GET"])
@login_required
def delete(user_id):
    update_time()
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    friends_list = current_user.friends.split(";")
    if str(user_id) in friends_list:
        del friends_list[friends_list.index(str(user_id))]
        user.friends = ";".join(friends_list)
    user2 = db_sess.query(User).filter(User.id == user_id).first()
    friends_list2 = user2.friends.split(";")
    if str(current_user.id) in friends_list2:
        del friends_list2[friends_list2.index(str(current_user.id))]
        user2.friends = ";".join(friends_list2)
    db_sess.commit()
    return redirect("/friends")


# функция восстановления пароля ( 1 этап ввод почты пользователя )
@app.route("/recovery", methods=["POST", "GET"])
def forgot_password():
    global CODE
    db_sess = db_session.create_session()
    form = FirstRecPswForm()
    alert = ""
    usr = False
    if form.validate_on_submit():
        try:
            usr = db_sess.query(User).filter(User.email == form.email.data).first()
            subject = "Смена пароля аккаунта"
            text = f"Здравствуйте, {usr.name}!\n" \
                   f"Код для смены пароля: {CODE}.\n" \
                   f"Если Вы не хотите менять пароль, просто проигнорируйте это сообщение."
            send_mail(usr.email, subject, text, [])
            return redirect(f"/recovery/code/{form.email.data}")
        except:
            if not usr:
                alert = f"Нет пользователя с почтой {form.email.data}"
            else:
                alert = f"Неполадки в работе сервера. Попробуйте снова"
    return render_template("recovery1.html",
                           form=form,
                           alert=alert,
                           title="Recovery",
                           recovery_title="Recovery password")


# функция восстановления пароля ( 2 этап ввод кода из сообщения )
@app.route("/recovery/code/<email>", methods=["POST", "GET"])
def recovery_code(email):
    global CODE
    db_sess = db_session.create_session()
    form = SecondRecPswForm()
    alert = ""
    usr = db_sess.query(User).filter(User.email == email).first()
    if form.validate_on_submit():
        if str(form.code.data) == CODE:
            CODE = generate_code()
            return redirect(f"/recovery/new-password/{usr.shortname}")
        else:
            alert = "Неверный код"
    return render_template("recovery2.html", form=form, alert=alert, title="Recovery")


# функция восстановления пароля ( 3 этап создание нового пароля )
@app.route("/recovery/new-password/<shortname>", methods=["POST", "GET"])
def new_password(shortname):
    db_sess = db_session.create_session()
    form = ThirdRecPswForm()
    alert = ""
    usr = db_sess.query(User).filter(User.shortname == shortname).first()
    if request.method == "POST":
        if form.validate_on_submit():
            usr.hashed_password = generate_password_hash(form.password.data)
            db_sess.commit()
            return redirect("/success/3")
        else:
            alert = "Заполните все поля!"
    return render_template("recovery3.html", alert=alert, title="Recovery", form=form)


# функция смены пароля ( ввод старого пароля для подтверждения )
# далее переадресация на 3 этап воссстановления пароля
@app.route("/settings/change-password", methods=["POST", "GET"])
@login_required
def change_password():
    db_sess = db_session.create_session()
    form = ChangePswForm()
    alert = ""
    usr = db_sess.query(User).filter(User.id == current_user.id).first()
    if request.method == "POST":
        if form.validate_on_submit():
            if usr.check_password(form.password.data):
                return redirect(f"/recovery/new-password/{usr.shortname}")
            else:
                alert = "Wrong password!"
        else:
            alert = "Enter your password."
    return render_template("change_password.html",
                           form=form,
                           title="Change password",
                           alert=alert)


# функция восстановления shortname
@app.route("/recovery/shortname", methods=["POST", "GET"])
def forgot_shortname():
    global CODE
    db_sess = db_session.create_session()
    form = FirstRecPswForm()
    alert = ""
    usr = False
    if form.validate_on_submit():
        try:
            usr = db_sess.query(User).filter(User.email == form.email.data).first()
            subject = "Восстановление аккаунта"
            text = f"Здравствуйте, {usr.name}!\n" \
                   f"Ваш shortname: {usr.shortname}\n" \
                   f"Используйте его для входа в аккаунт и не забывайте его."
            send_mail(usr.email, subject, text, [])
            return redirect(f"/success/1")
        except:
            if not usr:
                alert = f"Нет пользователя с почтой {form.email.data}"
            else:
                alert = f"Неполадки в работе сервера. Попробуйте снова"
    return render_template("recovery1.html",
                           form=form,
                           alert=alert,
                           title="Recovery",
                           recovery_title="Recovery shortname")


@app.route("/success/<int:mes_code>")
def success(mes_code):
    message = ""
    if mes_code == 1:
        message = "Expect an email letter with shortname( login) . Check your email."
    elif mes_code == 2:
        message = "You are registered in Hestia!"
    elif mes_code == 3:
        message = "Account details changed."
    return render_template("success.html", message=message)


@app.route("/profile/<shortname>", methods=["POST", "GET"])
def profile(shortname):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.shortname == shortname).first()
    date = user.modified_date.date()
    if user.friends != '':
        friends = user.friends.split(';')
    else:
        friends = []
    friends1 = []
    for i in friends:
        friends1.append(db_sess.query(User).filter(User.id == int(i)).first())
    if user.avatar is not None:
        avatar = f"/static/user_images/{user.shortname}/{user.avatar}"
    else:
        avatar = f"/static/user_images/anonym.jpg"
    news = db_sess.query(News).filter((News.user_shortname == user.shortname))
    if request.method == "POST":
        image = request.files["upload"]
        path = os.path.join(app.config["UPLOAD_FOLDER"] + f"{current_user.shortname}",
                            image.filename)
        image.save(path)
        current_user.avatar = f"{image.filename}"
        db_sess.merge(current_user)
        db_sess.commit()
        if user.avatar is not None:
            avatar = f"/static/user_images/{user.shortname}/{user.avatar}"
        else:
            avatar = f"/static/user_images/anonym.jpg"
    return render_template("me.html", user=user, date=date,
                           friends=friends1, len_friends=len(friends1),
                           avatar=avatar, news=news, title="Profile")


@app.route("/settings/change-profile", methods=["POST", "GET"])
def edit():
    form = EditForm()
    db_sess = db_session.create_session()
    if form.validate_on_submit():
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        if form.address.data != '':
            user.address = form.address.data
        if form.name.data != '':
            user.name = form.name.data
        if form.surname.data != '':
            user.surname = form.surname.data
        db_sess.add(user)
        db_sess.commit()
        return redirect(f"/profile/{user.shortname}")
    return render_template("edit.html", form=form, title="Edit")


@app.route("/profile/friends/<shortname>", methods=["POST", "GET"])
def profile_friends(shortname):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.shortname == shortname).first()
    friends = user.friends.split(';')
    friends1 = []
    for i in friends:
        friends1.append(db_sess.query(User).filter(User.id == int(i)).first())

    return render_template("profile_friends.html", friends=friends1, title="All friends")


@app.route('/news',  methods=['GET', 'POST'])
@login_required
def news():
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.is_private != True)
    return render_template("news.html", news=news)


@app.route('/add_news',  methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    db_sess = db_session.create_session()
    news = News()
    if form.validate_on_submit():
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data
        news.user_shortname = current_user.shortname
        hour = datetime.datetime.now().time().hour
        min = datetime.datetime.now().time().minute
        news.time = datetime.time(hour, min)
        try:
            img = form.image.data
            path = f"static/user_images/{current_user.shortname}/" + img.filename
            img.save(path)
            news.photo_name = img.filename
        except Exception:
            pass
        db_sess.add(news)
        db_sess.commit()
        return redirect('/news')
    return render_template('add_news.html', title='Добавление новости',
                           form=form, news=news)


@app.route('/edit_news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id,
                                      News.user == current_user
                                      ).first()
    if request.method == "GET":
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            try:
                img = form.image.data
                path = f"static/user_images/{current_user.shortname}/" + img.filename
                img.save(path)
                if news.photo_name != 0:
                    news.photo_name = ';'.join([news.photo_name, img.filename])
                else:
                    news.photo_name = img.filename
            except Exception:
                pass
            db_sess.commit()
            return redirect('/news')
        else:
            abort(404)
    return render_template('edit_news.html',
                           title='Редактирование новости',
                           form=form, news=news
                           )


@app.route('/del_news/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id,
                                      News.user == current_user
                                      ).first()
    if news:
        db_sess.delete(news)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/news')


@app.route("/photo/delete/<id>")
def photo_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id).first()
    news.photo_name = None
    db_sess.commit()
    return redirect(f'/edit_news/{id}')


if __name__ == "__main__":
    main()
