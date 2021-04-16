import datetime
from flask_wtf import FlaskForm
from wtforms import BooleanField, SubmitField
from wtforms import StringField, PasswordField
from wtforms import IntegerField, TextAreaField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, EqualTo, Email, Length


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    surname = StringField("Surname", validators=[DataRequired()])
    address = StringField("Locality")
    email = StringField("Email", validators=[DataRequired(), Email()])
    shortname = StringField("Short name - login")
    password = StringField("Password", validators=[DataRequired()])
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
