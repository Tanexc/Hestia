import datetime
from flask_wtf import FlaskForm
from wtforms import BooleanField, SubmitField
from wtforms import StringField, PasswordField
from wtforms import IntegerField, TextAreaField
from wtforms import FileField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, EqualTo, Email, Length, ValidationError


illegal_symbols = {"!", "/", "|", "("
                       "+", "=", "@", ">"
                       "№", "`", "'", "<"
                       '"', ";", ",", "."
                       "\\", "{", "}", ")"
                       "[", "]", "*", " "
                       "^", ":", "%", "&"
                       "$", "#", "?", }

illegal_passwords_parts = [
                    "1234", "zxc", "asdf",
                    "qwert", "0000", "3333",
                    "apple", "1111", "2222",
                    "pass", "сложн", "админ",
                    "word", "admin", "пароль"
]


def Shortname_validate(form, field):
    if len(list(illegal_symbols & set(list(field.data)))) != 0:
        raise ValidationError("Use only letters, numbers and symbols '_',  '-'")


def Password_validate(form, field):
    password = field.data
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")
    elif password.isalpha() and (password.islower() or password.isupper()) or password.isdigit():
        raise ValidationError("Use upper and lower letters, digits and other symbols")
    elif len(list(filter(lambda x: x in password.lower(), illegal_passwords_parts))) != 0:
        raise ValidationError("Simple password")


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    surname = StringField("Surname", validators=[DataRequired()])
    address = StringField("Locality*")
    email = StringField("Email", validators=[DataRequired(), Email()])
    shortname = StringField("Short name - login", validators=[DataRequired(), Shortname_validate])
    password = StringField("Password", validators=[DataRequired(), Password_validate])
    rep_password = StringField("Repeat password", validators=[DataRequired(),
                                                              EqualTo('password',
                               message="Passwords must match")])
    submit = SubmitField("Submit")


class FinishRegistration(FlaskForm):
    code = StringField("Code", validators=[DataRequired()])
    submit = SubmitField("Submit")


class LoginForm(FlaskForm):
    shortname = StringField('Short name - login', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Login')


class EditForm(FlaskForm):
    name = StringField("Name")
    surname = StringField("Surname")
    address = StringField("Locality*")
    about_me = StringField("About_me")
    submit = SubmitField("Submit")


class DialogForm(FlaskForm):
    input_line = TextAreaField('Type your message there', validators=[DataRequired(),
                                                                      Length(min=1,
                                                                             max=500)])
    submit = SubmitField('Send')


class SearchFriendForm(FlaskForm):
    input_line = StringField("Type user's name, surname or shortname",
                             validators=[DataRequired(),
                                         Length(min=1, max=30)])
    submit = SubmitField('Search')


class FirstRecPswForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Submit")


class SecondRecPswForm(FlaskForm):
    code = StringField("Code", validators=[DataRequired()])
    submit = SubmitField("Submit")


class ThirdRecPswForm(FlaskForm):
    password = StringField("Password", validators=[DataRequired()])
    rep_password = StringField("Repeat password",
                               validators=[DataRequired(),
                                           EqualTo('password',
                                                   message="Passwords must match")])
    submit = SubmitField("Submit")


class ChangePswForm(FlaskForm):
    password = StringField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")


class NewsForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField("Content", validators=[Length(min=0, max=256)])
    image = FileField('Photo')
    is_private = BooleanField("Private")
    submit = SubmitField('Submit')
