from flask import Flask, render_template, request, redirect, url_for, session, flash
from auth import authenticate, get_current_user, login_required, role_required, inject_auth_context
import config
from db import test_db_connection

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Registrar context processor → inyecta current_user, sidebar_menu, has_permission en todos los templates
app.context_processor(inject_auth_context)


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if get_current_user():
        return redirect(url_for('equipos'))

    if request.method == 'POST':
        username = request.form.get('usuario', '').strip()
        password = request.form.get('password', '')

        user = authenticate(username, password)
        if user:
            session['user'] = user
            return redirect(url_for('equipos'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente.', 'success')
    return redirect(url_for('login'))


@app.route('/equipos')
@login_required
@role_required('dashboard')
def equipos():
    return render_template('dashboard.html')


@app.route('/equipo/<id>')
@login_required
@role_required('equipo_detalle')
def equipo_detalle(id):
    return f"Vista de detalle del equipo {id} (En desarrollo)"


@app.route('/equipo/nuevo', methods=['GET', 'POST'])
@login_required
@role_required('equipo_nuevo')
def equipo_nuevo():
    return "Vista para crear un nuevo equipo (En desarrollo)"


@app.route('/equipo/<id>/editar', methods=['GET', 'POST'])
@login_required
@role_required('equipo_editar')
def equipo_editar(id):
    return f"Vista para editar el equipo {id} (En desarrollo)"


@app.route('/equipo/<id>/eliminar', methods=['POST'])
@login_required
@role_required('equipo_eliminar')
def equipo_eliminar(id):
    return f"Vista/Ruta para eliminar el equipo {id} (En desarrollo)"


@app.route('/solicitar-equipo', methods=['GET', 'POST'])
@login_required
@role_required('solicitar_equipo')
def solicitar_equipo():
    if request.method == 'POST':
        tipo = request.form.get('tipo')
        justificacion = request.form.get('justificacion')
        fecha_desde = request.form.get('fecha_desde')
        fecha_hasta = request.form.get('fecha_hasta')
        # Por ahora solo simulamos que la solicitud fue enviada exitosamente
        flash('Solicitud de equipo enviada exitosamente. Estado: Pendiente.', 'success')
        return redirect(url_for('asignaciones'))
    
    return render_template('solicitar_equipo.html')


@app.route('/asignaciones')
@login_required
@role_required('asignaciones')
def asignaciones():
    # En el futuro se obtendrán desde SQL Server, filtrando por current_user['rol']
    # y current_user['username'] si es necesario.
    return render_template('asignaciones.html')


# --- Stubs para enlaces del sidebar ---
@app.route('/componentes')
@login_required
@role_required('componentes')
def componentes():
    return render_template('stub.html', title='Componentes', message='Gestión de componentes en MongoDB (En desarrollo).')

@app.route('/mantenimiento')
@login_required
@role_required('mantenimiento')
def mantenimiento():
    return render_template('stub.html', title='Mantenimiento', message='Programación y registro de mantenimientos (En desarrollo).')

@app.route('/aulas')
@login_required
@role_required('aulas')
def aulas():
    return render_template('stub.html', title='Aulas / Laboratorios', message='Gestión de ubicación física de equipos (En desarrollo).')

@app.route('/responsables')
@login_required
@role_required('responsables')
def responsables():
    return render_template('stub.html', title='Responsables', message='Asignación de equipos a responsables (En desarrollo).')

@app.route('/reportes')
@login_required
@role_required('reportes')
def reportes():
    return render_template('stub.html', title='Reportes', message='Generación de reportes de inventario y estado (En desarrollo).')

@app.route('/usuarios')
@login_required
@role_required('usuarios')
def usuarios():
    return render_template('stub.html', title='Usuarios', message='Administración de cuentas (Active Directory/LDAP mock) (En desarrollo).')

@app.route('/configuracion')
@login_required
@role_required('configuracion')
def configuracion():
    return render_template('stub.html', title='Configuración', message='Ajustes del sistema (En desarrollo).')

@app.route('/health')
def health():
    db_ok = test_db_connection()
    status = 200 if db_ok else 503
    return {
        "status": "ok" if db_ok else "error",
        "sql_server": "connected" if db_ok else "disconnected",
        "auth_mode": config.AUTH_MODE
    }, status


# ── Manejo de errores ──────────────────────
@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
