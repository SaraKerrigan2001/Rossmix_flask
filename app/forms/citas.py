"""Formularios WTForms para el flujo de citas."""
from flask_wtf import FlaskForm
from wtforms import HiddenField, SubmitField
from wtforms.validators import DataRequired


class SeleccionarHorarioForm(FlaskForm):
    id_servicio = HiddenField(validators=[DataRequired()])
    id_empleado = HiddenField(validators=[DataRequired()])
    fecha = HiddenField(validators=[DataRequired()], render_kw={'id': 'fecha-hidden'})
    hora = HiddenField(validators=[DataRequired()], render_kw={'id': 'hora-hidden'})
    submit = SubmitField('Continuar a Confirmación →')


class ConfirmarCitaForm(FlaskForm):
    id_servicio = HiddenField(validators=[DataRequired()])
    id_empleado = HiddenField(validators=[DataRequired()])
    fecha_hora_inicio = HiddenField(validators=[DataRequired()])
    fecha_hora_fin = HiddenField(validators=[DataRequired()])
    submit = SubmitField('Confirmar y Agendar Cita')
