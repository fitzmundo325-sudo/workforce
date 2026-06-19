from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Log In')


ROLE_CHOICES = [
    ('requester', 'Requester (Store Staff)'),
    ('manager', 'Manager / Team Leader'),
    ('cluster_manager', 'Cluster Manager'),
    ('admin', 'Administrator'),
]


class RegisterForm(FlaskForm):
    full_name = StringField('Full Name', validators=[
                            DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[
                        DataRequired(), Email(), Length(max=120)])
    store_branch = StringField('Store Branch', validators=[
                               DataRequired(), Length(max=100)])
    role = SelectField('Role', choices=ROLE_CHOICES, validators=[DataRequired()])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=6, max=128)])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Register')
