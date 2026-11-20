from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, DateField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange

class GuestForm(FlaskForm):
    """Form for adding/editing guests"""
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    email = StringField('Email', validators=[Optional(), Length(max=120)])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=20)])
    id_proof_type = SelectField('ID Proof Type', 
                                choices=[('', 'Select ID Type'), 
                                        ('Aadhar Card', 'Aadhar Card'),
                                        ('PAN Card', 'PAN Card'), 
                                        ('Passport', 'Passport'),
                                        ('Driving License', 'Driving License'),
                                        ('Voter ID', 'Voter ID')],
                                validators=[Optional()])
    id_proof_number = StringField('ID Proof Number', validators=[Optional(), Length(max=50)])
    address = TextAreaField('Address', validators=[Optional()])
    submit = SubmitField('Save Guest')

class GuestNoteForm(FlaskForm):
    """Form for adding notes to guest profiles"""
    note_text = TextAreaField('Note', validators=[DataRequired(), Length(min=10, max=1000)])
    submit = SubmitField('Add Note')
