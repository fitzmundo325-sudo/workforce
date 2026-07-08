from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, RadioField, FileField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


PARTICULAR_JOB_CHOICES = [
    ('Cleaning', 'Cleaning'),
    ('Repair', 'Repair'),
    ('Replacement', 'Replacement'),
]

WARRANTY_CHOICES = [
    ('With Warranty', 'With Warranty'),
    ('Without Warranty', 'Without Warranty'),
    ('Other', 'Other'),
]

DEPARTMENT_CHOICES = [
    ('Store Maintenance', 'Store Maintenance'),
    ('Office Maintenance', 'Office Maintenance'),
    ('IT Concerns', 'IT Concerns'),
]

ASSET_TYPE_CHOICES = [
    ('Equipment', 'Equipment'),
    ('Structural', 'Structural'),
    ('Fix & Furnitures', 'Fix & Furnitures'),
]

TYPE_CHOICES = [
    ('', '-- Select Type --'),
    ('Chiller', 'Chiller'),
    ('Aircon', 'Aircon'),
    ('Showcase', 'Showcase'),
    ('Cabinet', 'Cabinet'),
    ('Sink', 'Sink'),
    ('Table', 'Table'),
    ('Chair', 'Chair'),
    ('Floor', 'Floor'),
    ('Wall', 'Wall'),
    ('Ceiling', 'Ceiling'),
    ('Door', 'Door'),
    ('Computer', 'Computer'),
]

URGENCY_CHOICES = [
    ('Minor', 'Minor'),
    ('Major', 'Major'),
    ('Critical', 'Critical'),
]


class WorkRequestSection1Form(FlaskForm):
    store_branch = StringField('Store Branch', validators=[DataRequired(), Length(max=100)])
    question_type = StringField('Question Type', validators=[Optional(), Length(max=100)])
    manager_name = StringField('Manager / Team Leader', validators=[DataRequired(), Length(max=100)])
    cluster_manager_name = StringField('Cluster Manager', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Full Description of the Problem', validators=[DataRequired()])
    particular_job = RadioField('Particular Job', choices=PARTICULAR_JOB_CHOICES, validators=[DataRequired()])
    warranty = RadioField('Warranty / Other', choices=WARRANTY_CHOICES, validators=[DataRequired()])
    warranty_other = StringField('Other Warranty', validators=[Optional(), Length(max=200)])
    department = RadioField('Department Concerned', choices=DEPARTMENT_CHOICES, validators=[DataRequired()])
    asset_type = RadioField('Asset Type', choices=ASSET_TYPE_CHOICES, validators=[DataRequired()])
    asset_detail_type = SelectField('Type', choices=TYPE_CHOICES, validators=[DataRequired()])
    urgency = RadioField('Urgency', choices=URGENCY_CHOICES, validators=[DataRequired()])
    submit = SubmitField('Next: Pictures & Signatures')


class WorkRequestSection2Form(FlaskForm):
    pictures = FileField('Pictures')
    manager_signature = HiddenField('Manager Signature')
    cm_signature = HiddenField('Cluster Manager Signature')
    submit = SubmitField('Submit Request')
    save_draft = SubmitField('Save as Draft')
