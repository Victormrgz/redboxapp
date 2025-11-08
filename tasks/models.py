from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from datetime import date
import uuid
from django.utils import timezone

# Create your models here.


class Profile(models.Model):
    ROLE_CHOICES = [
        ('user', 'Usuario'),
        ('coach', 'Coach'),
        ('admin', 'Administrador'),
    ]

    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]

    PLAN_CHOICES = [
        ('basic', 'Básico'),
        ('premium', 'Premium'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=10, choices=ROLE_CHOICES, default='user')
    phone = models.CharField(max_length=20, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    identity_card = models.CharField(max_length=20, blank=True)
    weight = models.FloatField(null=True, blank=True)  # en kilogramos
    height = models.FloatField(null=True, blank=True)  # en metros
    creditos = models.PositiveIntegerField(default=0)  # créditos iniciales

    # Suscripción
    plan = models.CharField(
        max_length=10, choices=PLAN_CHOICES, default='basic')
    activated_on = models.DateField(null=True, blank=True)
    expires_on = models.DateField(null=True, blank=True)

    @property
    def is_activo(self):
        return self.expires_on and self.expires_on >= date.today()

    def calcular_imc(self):
        if self.weight and self.height and self.height > 0:
            height_m = self.height / 100  # convertir cm a metros
            return round(self.weight / (height_m ** 2), 2)
        return None

    def reservas_restantes(self):
        if not self.activated_on or not self.expires_on:
            return 0

        total = 12 if self.plan == 'basic' else 24
        usadas = Reservation.objects.filter(
            user=self.user,
            date__gte=self.activated_on,
            date__lt=self.expires_on
        ).count()
        return max(0, total - usadas)

    def activar_suscripcion(self):
        self.activated_on = date.today()
        self.expires_on = date.today() + timedelta(days=30)
        self.save()

    def desactivar_suscripcion(self):
        self.expires_on = None
        self.save()

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    time_slot = models.TimeField()

    def __str__(self):
        return f"{self.user.username} - {self.date} {self.time_slot}"


class Planificacion(models.Model):
    fecha = models.DateField(unique=True)
    contenido = models.TextField()

    def __str__(self):
        return f"Planificación para {self.fecha}"


class Pago(models.Model):
    MONEDAS = [
        ('VES', 'Bolívares'),
        ('USD', 'Dólares'),
        ('COP', 'Pesos'),
    ]

    perfil = models.ForeignKey(
        Profile, null=True, blank=True, on_delete=models.SET_NULL)
    fecha_pago = models.DateField(auto_now_add=True)
    monto = models.DecimalField(max_digits=8, decimal_places=2)
    moneda = models.CharField(max_length=3, choices=MONEDAS, default='VES')
    plan = models.CharField(max_length=10, choices=Profile.PLAN_CHOICES)
    nombre_usuario = models.CharField(max_length=100, null=True, blank=True)
    correo_usuario = models.EmailField(null=True, blank=True)

    def aplicar_suscripcion(self):
        self.perfil.plan = self.plan
        self.perfil.activated_on = self.fecha_pago
        self.perfil.expires_on = self.fecha_pago + timedelta(days=30)

        # Asignar créditos según el plan
        if self.plan == 'basic':
            self.perfil.creditos = 12
        elif self.plan == 'premium':
            self.perfil.creditos = 24
        else:
            self.perfil.creditos = 0  # por seguridad

        self.perfil.save()

    def __str__(self):
        return f"Pago de {self.perfil.user.username} ({self.plan} - {self.moneda})"


class LiftResult(models.Model):
    MOVEMENT_CHOICES = [
        ('Snatch', 'Snatch'),
        ('Power Snatch', 'Power Snatch'),
        ('Clean & Jerk', 'Clean & Jerk'),
        ('Clean', 'Clean'),
        ('Power Clean', 'Power Clean'),
        ('Back Squat', 'Back Squat'),
        ('Front Squat', 'Front Squat'),
        ('Deadlift', 'Deadlift'),
        ('Bench Press', 'Bench Press'),
        ('Push Jerk', 'Push Jerk'),
        ('Split Jerk', 'Split Jerk'),
        ('Shoulder Press', 'Shoulder Press'),
    ]

    UNITS = [('kg', 'kg'), ('lb', 'lb')]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movement = models.CharField(max_length=50, choices=MOVEMENT_CHOICES)
    date = models.DateField()
    rounds = models.PositiveIntegerField()
    reps = models.PositiveIntegerField()
    weight = models.FloatField()
    unit = models.CharField(max_length=2, choices=UNITS)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.movement} - {self.weight}{self.unit} ({self.date})"


class Invitacion(models.Model):
    codigo = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    usado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.codigo)

    def esta_activa(self):
        if self.usado:
            return False
        if self.fecha_expiracion and timezone.now() > self.fecha_expiracion:
            return False
        return True


class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        from django.utils import timezone
        return timezone.now() - self.created_at < timezone.timedelta(minutes=10)
