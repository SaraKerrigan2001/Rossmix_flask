"""Formularios de autenticación y pagos usando Flask-WTF."""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DecimalField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional


class LoginForm(FlaskForm):
    email = StringField('Correo electrónico', validators=[DataRequired(message='El email es obligatorio'), Email(message='Correo inválido')])
    password = PasswordField('Contraseña', validators=[DataRequired(message='La contraseña es obligatoria')])
    submit = SubmitField('Iniciar Sesión')


class RegisterForm(FlaskForm):
    nombre = StringField('Nombre completo', validators=[DataRequired(message='El nombre es obligatorio'), Length(min=3, max=100)])
    email = StringField('Correo electrónico', validators=[DataRequired(message='El email es obligatorio'), Email(message='Correo inválido')])
    telefono = StringField('Teléfono', validators=[DataRequired(message='El teléfono es obligatorio'), Length(min=6, max=20)])
    password = PasswordField('Contraseña', validators=[DataRequired(message='La contraseña es obligatoria'), Length(min=6, message='La contraseña debe tener al menos 6 caracteres')])
    confirmar_password = PasswordField('Confirmar contraseña', validators=[DataRequired(message='La confirmación es obligatoria'), EqualTo('password', message='Las contraseñas no coinciden')])
    submit = SubmitField('Crear Cuenta')


class PagoForm(FlaskForm):
    monto = DecimalField('Monto', validators=[DataRequired(message='El monto es obligatorio'), NumberRange(min=1, message='El monto debe ser mayor a 0')])
    metodo_pago = SelectField(
        'Método de pago',
        choices=[
            ('efectivo', 'Efectivo'),
            ('tarjeta', 'Tarjeta'),
            ('transferencia', 'Transferencia'),
            ('nequi', 'Nequi'),
            ('daviplata', 'Daviplata'),
        ],
        validators=[DataRequired(message='El método de pago es obligatorio')]
    )
    referencia = StringField('Referencia', validators=[Optional(), Length(max=100)])
    notas = TextAreaField('Notas', validators=[Optional(), Length(max=400)])
    submit = SubmitField('Confirmar Pago')
