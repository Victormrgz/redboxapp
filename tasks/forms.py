from django.forms import ModelForm
from django import forms
from django.contrib.auth.forms import UserCreationForm
# pylint: disable=imported-auth-user
from django.contrib.auth.models import User
from .models import Reservation, Planificacion, Profile, LiftResult, Invitacion
from datetime import date, timedelta, datetime, time
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class CustomUserCreationForm(UserCreationForm):
    codigo_invitacion = forms.UUIDField(label=_("Código de invitación"))
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name",
                  "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'Nombre de usuario'
        self.fields['first_name'].widget.attrs['placeholder'] = 'Nombre'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Apellido'
        self.fields['email'].widget.attrs['placeholder'] = 'Correo electrónico'
        self.fields['password1'].widget.attrs['placeholder'] = 'Contraseña'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirmar contraseña'
        self.fields['password1'].error_messages = {
            'required': _('Este campo es obligatorio.'),
            'password_too_short': _('La contraseña es muy corta. Debe tener al menos 8 caracteres.'),
            'password_too_common': _('Esta contraseña es demasiado común.'),
            'password_entirely_numeric': _('La contraseña no puede ser completamente numérica.'),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "Ya existe una cuenta con este correo.")
        return email

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name', '')
        return first_name.strip().title()

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name', '')
        return last_name.strip().title()

    def clean_codigo_invitacion(self):
        codigo = self.cleaned_data.get('codigo_invitacion')
        try:
            invitacion = Invitacion.objects.get(codigo=codigo)
        except Invitacion.DoesNotExist:
            raise forms.ValidationError(
                "El código de invitación no es válido.")

        if not invitacion.esta_activa():
            raise forms.ValidationError(
                "Este código ya fue usado o ha expirado.")

        self.invitacion = invitacion  # guardamos para usar en la vista
        return codigo


class FlexibleAuthForm(forms.Form):
    identifier = forms.CharField(
        label="Username or Email",
        widget=forms.TextInput(attrs={'placeholder': 'Usuario o correo'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Contraseña'})
    )


# CLASSES

TIME_CHOICES = [
    ("06:00", "6:00"),
    ("07:00", "7:00"),
    ("08:00", "8:00"),
    ("09:00", "9:00"),
    ("10:00", "10:00"),
    ("15:00", "15:00"),
    ("16:00", "16:00"),
    ("17:00", "17:00"),
    ("18:00", "18:00"),
    ("19:00", "19:00"),
]

MAX_RESERVAS_POR_HORARIO = 18


class ReservationForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.TextInput(attrs={
            'type': 'date',
            'id': 'id_date',
            'class': 'input-field',
        }),
        label="Fecha"
    )
    time_slot = forms.ChoiceField(
        choices=TIME_CHOICES,
        widget=forms.Select(attrs={
            'id': 'id_time_slot',
            'class': 'input-field select-horario'
        }),
        label="Horario"
    )

    class Meta:
        model = Reservation
        fields = ['date', 'time_slot']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        time_slot = cleaned_data.get('time_slot')

        if not date or not time_slot or not self.user:
            return cleaned_data

        hoy = timezone.localdate()
        ahora = timezone.localtime().time()

        # No permitir domingos
        if date.weekday() == 6:
            raise forms.ValidationError(
                "No se pueden hacer reservas los domingos.")

        # No permitir fechas pasadas
        if date < hoy:
            raise forms.ValidationError("No puedes reservar días pasados.")

        # No permitir más de una reserva por día
        ya_tiene_reserva_en_dia = Reservation.objects.filter(
            user=self.user,
            date=date
        ).exists()

        if ya_tiene_reserva_en_dia:
            raise forms.ValidationError(
                "Ya tienes una reserva registrada para ese día.")

        # Convertir time_slot si es string
        if isinstance(time_slot, str):
            try:
                time_slot = datetime.strptime(time_slot, "%H:%M").time()
                cleaned_data['time_slot'] = time_slot
            except ValueError:
                raise forms.ValidationError("Formato de hora inválido.")

            # No permitir reservar horas que ya pasaron en el día actual
        if date == hoy and time_slot <= ahora:
            raise forms.ValidationError(
                "No puedes reservar una hora que ya ha pasado.")

            # ✅ Paso 2: Validar límite de reservas por horario
        reservas_en_horario = Reservation.objects.filter(
            date=date,
            time_slot=time_slot
        ).count()

        if reservas_en_horario >= MAX_RESERVAS_POR_HORARIO:
            raise forms.ValidationError(
                "Este horario ya está lleno. Elige otro.")

        return cleaned_data


class PlanificacionForm(forms.ModelForm):
    contenido = forms.CharField(required=False)

    class Meta:
        model = Planificacion
        fields = ['fecha', 'contenido']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'input-field'}),
            'contenido': forms.Textarea(attrs={
                'rows': 6,
                'class': 'input-field',
                'placeholder': 'Descripción opcional'
            }),
        }


class PerfilForm(forms.ModelForm):
    phone = forms.CharField(required=False)
    birth_date = forms.DateField(required=False)
    gender = forms.ChoiceField(choices=Profile.GENDER_CHOICES, required=False)
    identity_card = forms.CharField(required=False)
    weight = forms.FloatField(required=False)
    height = forms.FloatField(required=False)

    class Meta:
        model = Profile
        fields = ['phone', 'birth_date', 'gender',
                  'identity_card', 'weight', 'height']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'input-field',
                'pattern': '[0-9]*',
                'title': 'Solo números',
                'inputmode': 'numeric',
                'placeholder': '04121234567'
            }),
            'birth_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'input-field'
            }),
            'gender': forms.Select(attrs={'class': 'input-field'}),
            'identity_card': forms.TextInput(attrs={
                'class': 'input-field',
                'pattern': '[0-9]*',
                'title': 'Solo números',
                'inputmode': 'numeric',
                'placeholder': '12345678'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'input-field',
                'step': '0.1',
                'inputmode': 'decimal',
                'placeholder': 'kg'
            }),
            'height': forms.NumberInput(attrs={
                'class': 'input-field',
                'step': '0.01',
                'inputmode': 'decimal',
                'placeholder': 'cm'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone'].label = 'Teléfono'
        self.fields['birth_date'].label = 'Fecha de nacimiento'
        self.fields['gender'].label = 'Género'
        self.fields['identity_card'].label = 'Cédula'
        self.fields['weight'].label = 'Peso'
        self.fields['height'].label = 'Altura'

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not phone.isdigit():
            raise forms.ValidationError(
                "El número de teléfono debe contener solo dígitos.")
        return phone

    def clean_identity_number(self):
        number = self.cleaned_data.get('identity_number')
        if number and not number.isdigit():
            raise forms.ValidationError(
                "La cédula debe contener solo dígitos.")
        return number

    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight in ['', None]:
            return None
        try:
            weight = float(weight)
            if weight <= 0:
                raise forms.ValidationError("El peso debe ser mayor a cero.")
            return weight
        except ValueError as exc:
            raise forms.ValidationError("Ingresa un peso válido.") from exc

    def clean_height(self):
        height = self.cleaned_data.get('height')
        if height in ['', None]:
            return None
        try:
            height = float(height)
            if height <= 0:
                raise forms.ValidationError("La altura debe ser mayor a cero.")
            return height
        except ValueError as exc:
            raise forms.ValidationError("Ingresa una altura válida.") from exc


ROLE_CHOICES = [
    ('Usuario', 'Usuario'),
    ('Coach', 'Coach'),
    ('Administrador', 'Administrador'),
]


class RoleUpdateForm(forms.Form):
    new_role = forms.ChoiceField(choices=ROLE_CHOICES)
    pin = forms.CharField(required=False, widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self.current_role = kwargs.pop('current_role', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        new_role = cleaned_data.get('new_role')
        pin = cleaned_data.get('pin')

        if new_role == 'Administrador':
            if not pin:
                raise forms.ValidationError(
                    "Debes ingresar el PIN para asignar el rol de Administrador.")
            if pin != "1234":  # Puedes mover esto a settings o usar una variable segura
                raise forms.ValidationError("PIN incorrecto.")
        return cleaned_data


class LiftResultForm(forms.ModelForm):
    class Meta:
        model = LiftResult
        fields = ['movement', 'date', 'rounds', 'reps', 'weight', 'unit']
        labels = {
            'movement': 'Movimiento',
            'date': 'Fecha',
            'rounds': 'Rondas',
            'reps': 'Repeticiones',
            'weight': 'Peso',
            'unit': 'Unidad',
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'input-field'}),
            'movement': forms.Select(attrs={'class': 'input-field'}),
            'rounds': forms.NumberInput(attrs={'class': 'input-field'}),
            'reps': forms.NumberInput(attrs={'class': 'input-field'}),
            'weight': forms.NumberInput(attrs={'class': 'input-field', 'step': '0.5'}),
            'unit': forms.Select(attrs={'class': 'input-field'}),
        }
