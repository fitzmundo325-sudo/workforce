from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class SupplyRequestForm(FlaskForm):
    store_branch = StringField('Store Branch', validators=[DataRequired(), Length(max=100)])
    manager_name = StringField('Manager / Team Leader', validators=[DataRequired(), Length(max=100)])
    cluster_manager_name = StringField('Cluster Manager', validators=[DataRequired(), Length(max=100)])
    purpose = TextAreaField('Purpose / Reason', validators=[DataRequired()])
    items_data = HiddenField('Items Data', validators=[DataRequired()])
    manager_signature = HiddenField('Manager Signature')
    cm_signature = HiddenField('Cluster Manager Signature')
    submit = SubmitField('Submit Request')
    save_draft = SubmitField('Save as Draft')
