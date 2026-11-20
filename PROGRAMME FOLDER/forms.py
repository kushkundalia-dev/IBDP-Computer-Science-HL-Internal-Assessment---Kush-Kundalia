from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from models import User

class LoginForm(FlaskForm):
    """Login form"""
    email = StringField('Email', 
                       validators=[DataRequired(), Email()])
    password = PasswordField('Password', 
                            validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegisterForm(FlaskForm):
    """Registration form"""
    email = StringField('Email', 
                       validators=[DataRequired(), Email(), Length(max=120)])
    first_name = StringField('First Name', 
                            validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', 
                           validators=[DataRequired(), Length(max=50)])
    phone = StringField('Phone Number', 
                       validators=[Length(max=20)])
    password = PasswordField('Password', 
                            validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                    validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', 
                      choices=[('3', 'Front Desk Agent'), ('2', 'General Manager'), ('1', 'HR Manager')],
                      validators=[DataRequired()])
    submit = SubmitField('Register')
    
    def validate_email(self, email):
        """Check if email already exists"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')
