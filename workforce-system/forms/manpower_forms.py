from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, RadioField, DateField, IntegerField, HiddenField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
import datetime


NAME_TYPE_CHOICES = [
    ('', '-- Select --'),
    ('Promotion', 'Promotion'),
    ('Replacement', 'Replacement'),
    ('Transfer', 'Transfer'),
]

ADDITIONAL_CHOICES = [
    ('Promotion', 'Promotion'),
    ('Replacement', 'Replacement'),
    ('Transfer', 'Transfer'),
    ('Seasonal', 'Seasonal'),
    ('New Store', 'New Store'),
]


class ManpowerRequestSection1Form(FlaskForm):
    store_branch = StringField('Department / Store Requesting', validators=[DataRequired(), Length(max=100)])
    question_type = StringField('Question Type', validators=[Optional(), Length(max=100)])
    manager_name = StringField('Manager', validators=[DataRequired(), Length(max=100)])
    cluster_manager_name = StringField('Cluster Manager', validators=[DataRequired(), Length(max=100)])
    name_type = SelectField('Name (Promotion / Replacement / Transfer)', choices=NAME_TYPE_CHOICES, validators=[DataRequired()])
    reason = TextAreaField('Reason', validators=[DataRequired()])
    reason_detail = TextAreaField('Reason For Request', validators=[DataRequired()])
    additional = SelectMultipleField('Additional', choices=ADDITIONAL_CHOICES, validators=[Optional()])
    submit = SubmitField('Next: Employee Details & Signatures')


class ManpowerRequestSection2Form(FlaskForm):
    position_title = StringField('Position Title', validators=[DataRequired(), Length(max=100)])
    department_store = StringField('Department / Store', validators=[DataRequired(), Length(max=100)])
    company = StringField('Company', validators=[DataRequired(), Length(max=100)])
    date_required = DateField('Date Required', validators=[DataRequired()], default=datetime.date.today)
    employees_needed = IntegerField('No. of Employees Needed', validators=[DataRequired(), NumberRange(min=1, max=10)])
    existing_headcount = IntegerField('Dept. / Store Existing Headcount', validators=[DataRequired(), NumberRange(min=1, max=10)])
    manager_signature = HiddenField('Manager Signature')
    cm_signature = HiddenField('Cluster Manager Signature')
    submit = SubmitField('Submit Request')
    save_draft = SubmitField('Save as Draft')
