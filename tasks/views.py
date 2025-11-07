# Views

from collections import defaultdict
from django.utils.formats import date_format
from datetime import datetime, timedelta
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from datetime import date, datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from .models import Reservation, Planificacion, Profile, Pago, LiftResult, Invitacion
from django.core.exceptions import ObjectDoesNotExist
from .forms import CustomUserCreationForm, FlexibleAuthForm, LiftResultForm, ReservationForm, PlanificacionForm, PerfilForm
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
User = get_user_model()


# Create your views here.

@login_required
def gestionar_roles(request):
    if request.user.profile.role != 'admin':
        return redirect('dashboard')

    perfiles = Profile.objects.select_related('user').all()

    if request.method == 'POST':
        perfil_id = request.POST.get('perfil_id')
        nuevo_rol = request.POST.get('role')
        pin = request.POST.get('pin', '').strip()

        perfil = get_object_or_404(Profile, id=perfil_id)

        # Validar PIN para cualquier cambio de rol
        if not pin:
            messages.error(
                request, "Debes ingresar el PIN para modificar el rol.")
            return redirect('gestionar_roles')
        if pin != "1234":  # Puedes mover esto a settings.py
            messages.error(request, "PIN incorrecto.")
            return redirect('gestionar_roles')

        perfil.role = nuevo_rol
        perfil.save()
        messages.success(
            request, f"Rol actualizado para {perfil.user.username}")
        return redirect('gestionar_roles')

    return render(request, 'gestionar_roles.html', {
        'perfiles': perfiles,
        'usuario_actual': request.user
    })


@login_required
def editar_perfil(request):
    profile = request.user.profile

    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect('dashboard')
    else:
        form = PerfilForm(instance=profile)

    return render(request, 'editar_perfil.html', {
        'form': form,
        'profile': profile
    })


@login_required
def ver_planificacion(request):
    fecha = request.GET.get('fecha')
    planificacion = None

    if fecha:
        planificacion = Planificacion.objects.filter(fecha=fecha).first()

    return render(request, 'ver_planificacion.html', {
        'planificacion': planificacion,
        'fecha': fecha
    })


@login_required
def home(request):
    return render(request, 'home.html')


@login_required
def myreservations(request):
    hoy = timezone.localdate()
    ahora = timezone.localtime()

    reservas = Reservation.objects.filter(
        user=request.user).order_by('-date', '-time_slot')

    reservas_por_mes = defaultdict(list)

    for r in reservas:
        fecha_hora = datetime.combine(r.date, r.time_slot)
        if timezone.is_naive(fecha_hora):
            fecha_hora = timezone.make_aware(fecha_hora)

        if hasattr(r, 'cancelada') and r.cancelada:
            estado = "Cancelada"
        elif fecha_hora < ahora:
            estado = "Asistió"
        else:
            estado = "Pendiente"

        mes = date_format(r.date, "F Y", use_l10n=True)

        reservas_por_mes[mes].append({
            'id': r.id,
            'fecha': r.date,
            'hora': r.time_slot,
            'estado': estado
        })

    # Resumen mensual
    reservas_mes = reservas.filter(date__month=hoy.month, date__year=hoy.year)
    creditos_usados = reservas_mes.count()

    request.user.profile.refresh_from_db()
    creditos_disponibles = request.user.profile.creditos

    return render(request, 'myreservations.html', {
        'reservas_por_mes': dict(reservas_por_mes),
        'creditos_usados': creditos_usados,
        'creditos_disponibles': creditos_disponibles,
    })


@login_required
def myresults(request):
    return render(request, 'myresults.html')


def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html', {
            'form': CustomUserCreationForm()
        })
    else:
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            invitacion = form.invitacion
            invitacion.usado = True
            invitacion.save()

            login(request, user)
            return redirect('signin')
        else:
            return render(request, 'signup.html', {
                'form': form,
                'error': 'Revisa los campos con errores'
            })


def signout(request):
    logout(request)
    return redirect('signin')


def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html', {
            'form': FlexibleAuthForm()
        })
    else:
        form = FlexibleAuthForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['identifier']
            password = form.cleaned_data['password']

            # Detectar si es email
            if '@' in identifier:
                try:
                    user_obj = User.objects.get(email__iexact=identifier)
                    username = user_obj.username
                except ObjectDoesNotExist:
                    username = None
            else:
                try:
                    user_obj = User.objects.get(username__iexact=identifier)
                    username = user_obj.username
                except ObjectDoesNotExist:
                    username = None

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('dashboard')

        return render(request, 'signin.html', {
            'form': form,
            'error': 'Usuario o contraseña incorrectos'
        })


@login_required
def registrar_pago(request):
    if request.user.profile.role != 'admin':
        return redirect('dashboard')

    perfiles = Profile.objects.select_related('user').all()

    if request.method == 'POST':
        perfil_id = request.POST.get('perfil_id')
        plan = request.POST.get('plan')
        monto = request.POST.get('monto')
        moneda = request.POST.get('moneda')
        pin = request.POST.get('pin', '').strip()

        if not pin:
            messages.error(
                request, "Debes ingresar el PIN para registrar el pago.")
            return redirect('registrar_pago')
        if pin != "1234":
            messages.error(request, "PIN incorrecto.")
            return redirect('registrar_pago')

        perfil = get_object_or_404(Profile, id=perfil_id)

        pago = Pago.objects.create(
            perfil=perfil,
            nombre_usuario=perfil.user.get_full_name(),
            correo_usuario=perfil.user.email,
            plan=plan,
            monto=monto,
            moneda=moneda
        )

        pago.aplicar_suscripcion()

        messages.success(
            request, f"Pago registrado y suscripción activada para {perfil.user.username}")
        return redirect('registrar_pago')

    return render(request, 'registrar_pago.html', {
        'perfiles': perfiles
    })


@login_required
def historial_pagos(request):
    if request.user.profile.role != 'admin':
        return redirect('dashboard')

    usuario_id = request.GET.get('usuario_id')
    pagos = Pago.objects.select_related('perfil__user').order_by('-fecha_pago')

    if usuario_id:
        pagos = pagos.filter(perfil_id=usuario_id)

    perfiles = Profile.objects.select_related('user').all()

    return render(request, 'historial_pagos.html', {
        'pagos': pagos,
        'perfiles': perfiles,
        'usuario_id': int(usuario_id) if usuario_id else None
    })

# CLASSES


@login_required
def reserve_class(request):
    profile = request.user.profile
    if not profile.is_activo:
        messages.error(
            request, "Parece que tu suscripción no está activa en este momento. Para resolverlo rápidamente, <a href='https://wa.me/584121208635' target='_blank'>contáctanos aquí.</a>")
        return redirect('dashboard')

    if profile.reservas_restantes() <= 0:
        messages.error(
            request, "Has alcanzado el límite de reservas para este mes.")
        return redirect('dashboard')

    reservations = []
    selected_date = request.POST.get('date') or request.GET.get('date')
    selected_time = request.POST.get(
        'time_slot') or request.GET.get('time_slot')
    show_errors = False
    planificacion = None

    form = ReservationForm(request.POST or None, user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'reserve':
            if form.is_valid():
                Reservation.objects.create(
                    user=request.user,
                    date=selected_date,
                    time_slot=selected_time
                )
                # Descontar 1 crédito al reservar
                # Descontar crédito
                profile.creditos -= 1
                profile.save()

                form = ReservationForm(user=request.user)
            else:
                show_errors = True

    # Convertir la fecha a objeto date
    if selected_date:
        try:
            fecha_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except ValueError:
            fecha_obj = date.today()
    else:
        fecha_obj = date.today()

    # Buscar reservas y planificación
    if selected_time:
        reservations = Reservation.objects.filter(
            date=fecha_obj,
            time_slot=selected_time
        )

    planificacion_obj = Planificacion.objects.filter(fecha=fecha_obj).first()
    planificacion = planificacion_obj.contenido if planificacion_obj else None

    return render(request, 'classes.html', {
        'form': form,
        'reservations': reservations,
        'selected_date': selected_date,
        'selected_time': selected_time,
        'show_errors': show_errors,
        'planificacion': planificacion
    })


@login_required
def dashboard(request):
    user_reservas = Reservation.objects.filter(
        user=request.user
    ).order_by('-date', '-time_slot')[:5]

    fecha_actual = date.today()
    profile = request.user.profile
    imc = profile.calcular_imc()
    creditos_restantes = profile.reservas_restantes()

    context = {
        'ultimas_reservas': user_reservas,
        'fecha_actual': fecha_actual,
        'profile': profile,
        'imc': imc,
        'creditos_restantes': creditos_restantes,
    }
    return render(request, 'dashboard.html', context)


@login_required
def cancelar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reservation, id=reserva_id, user=request.user)

    # Combinar fecha y hora en un solo datetime
    horario_reserva = datetime.combine(reserva.date, reserva.time_slot)
    horario_reserva = timezone.make_aware(horario_reserva) if timezone.is_naive(
        horario_reserva) else timezone.localtime(horario_reserva)

    ahora = timezone.now()
    limite_cancelacion = horario_reserva - timedelta(minutes=30)

    # Determinar origen para redirección
    origen = request.POST.get('origen')
    destino = origen if origen in [
        'dashboard', 'myreservations'] else 'dashboard'

    if ahora > limite_cancelacion:
        messages.error(
            request, "No puedes cancelar esta reserva. El plazo máximo para cancelar es 30 minutos antes del inicio.")
        return redirect(destino)

    # Devolver crédito al usuario
    profile = request.user.profile
    profile.creditos += 1
    profile.save()

    reserva.delete()
    messages.success(request, "La clase ha sido cancelada correctamente.")
    return redirect(destino)


@login_required
def crear_planificacion(request):
    if request.user.profile.role not in ['admin', 'coach']:
        return redirect('dashboard')

    planificacion = None
    form = PlanificacionForm()

    # Si se recibe fecha por GET, precargar planificación
    fecha = request.GET.get('fecha')
    if fecha:
        planificacion = Planificacion.objects.filter(fecha=fecha).first()
        if planificacion:
            form = PlanificacionForm(instance=planificacion)
        else:
            form = PlanificacionForm(initial={'fecha': fecha})

    if request.method == 'POST':
        fecha = request.POST.get('fecha')
        contenido = request.POST.get('contenido', '').strip()

        planificacion = Planificacion.objects.filter(fecha=fecha).first()

        if planificacion:
            if contenido == '':
                planificacion.delete()
                messages.success(request, "Planificación eliminada.")
                return redirect('crear_planificacion')
            else:
                form = PlanificacionForm(request.POST, instance=planificacion)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Planificación actualizada.")
                    return redirect('crear_planificacion')
        else:
            if contenido != '':
                form = PlanificacionForm(request.POST)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Planificación creada.")
                    return redirect('crear_planificacion')

    return render(request, 'crear_planificacion.html', {
        'form': form,
        'planificacion': planificacion
    })


@login_required
def gestionar_suscripciones(request):
    if request.user.profile.role != 'admin':
        return redirect('dashboard')

    perfiles = Profile.objects.select_related('user').all()

    return render(request, 'gestionar_suscripciones.html', {
        'perfiles': perfiles,
        'usuario_actual': request.user
    })


@login_required
def add_result(request):
    if request.method == 'POST':
        form = LiftResultForm(request.POST)
        if form.is_valid():
            result = form.save(commit=False)
            result.user = request.user
            result.save()
            messages.success(request, "Resultado guardado correctamente.")
            return redirect('my_results')
    else:
        form = LiftResultForm()
    return render(request, 'add_result.html', {'form': form})


@login_required
def my_results(request):
    form = LiftResultForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        nuevo = form.save(commit=False)
        nuevo.user = request.user
        nuevo.save()
        messages.success(request, "Resultado guardado correctamente.")
        return redirect('my_results')

    # Obtener PRs por movimiento
    movimientos = LiftResult.MOVEMENT_CHOICES
    prs = []
    for key, label in movimientos:
        pr = LiftResult.objects.filter(
            user=request.user, movement=key).order_by('-weight').first()
        if pr:
            prs.append({
                'label': label,
                'weight': pr.weight,
                'unit': pr.unit,
                'date': pr.date
            })

    return render(request, 'my_results.html', {
        'form': form,
        'prs': prs,
    })


@login_required
def detalle_resultados(request):
    movimientos = LiftResult.MOVEMENT_CHOICES
    selected = request.GET.get('movement')
    resultados = LiftResult.objects.filter(user=request.user)

    if selected:
        resultados = resultados.filter(movement=selected)

    # ✅ Obtener el levantamiento con mayor peso del movimiento seleccionado
    ultimo = resultados.order_by('-weight').first()

    porcentajes = []
    if ultimo:
        base = ultimo.weight
        porcentajes = [
            {'porcentaje': f"{p}%", 'peso': round(base * p / 100, 2)}
            for p in [55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
        ]

    return render(request, 'detalle_resultados.html', {
        'resultados': resultados,
        'movimientos': movimientos,
        'selected': selected,
        'porcentajes': porcentajes,
        'ultimo': ultimo,
    })


@login_required
def eliminar_levantamiento(request, id):
    levantamiento = get_object_or_404(LiftResult, id=id, user=request.user)
    levantamiento.delete()
    messages.success(request, "Levantamiento eliminado correctamente.")
    return redirect('detalle_resultados')


@staff_member_required
def gestionar_invitaciones(request):
    if request.method == 'POST':
        nueva = Invitacion.objects.create()
        return redirect('gestionar_invitaciones')

    invitaciones = Invitacion.objects.order_by('-fecha_creacion')
    return render(request, 'admin_invitaciones.html', {
        'invitaciones': invitaciones
    })


@staff_member_required
def eliminar_invitacion(request, invitacion_id):
    invitacion = get_object_or_404(Invitacion, id=invitacion_id)
    if not invitacion.usado:
        invitacion.delete()
    return redirect('gestionar_invitaciones')


@staff_member_required
@login_required
def eliminar_usuario(request, usuario_id):
    if request.method == 'POST':
        pin = request.POST.get('pin', '').strip()
        if not pin:
            messages.error(
                request, "Debes ingresar el PIN para eliminar el usuario.")
            return redirect('gestionar_roles')
        if pin != "1234":
            messages.error(request, "PIN incorrecto.")
            return redirect('gestionar_roles')

        usuario = get_object_or_404(User, id=usuario_id)
        if not usuario.is_superuser and usuario != request.user:
            usuario.delete()
            messages.success(request, "Usuario eliminado correctamente.")
        else:
            messages.error(request, "No puedes eliminar este usuario.")
    return redirect('gestionar_roles')
