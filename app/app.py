from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from auth import authenticate, get_current_user, login_required, role_required, inject_auth_context
import config
from db import (
    test_db_connection, get_db_connection,
    test_mongo_connection, get_all_hardware, get_hardware_by_id,
    insert_hardware, update_hardware, delete_hardware
)
import datetime

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Registrar context processor → inyecta current_user, sidebar_menu, has_permission en todos los templates
app.context_processor(inject_auth_context)


def get_dashboard_stats():
    conn = get_db_connection()
    stats = {
        'total_equipos': 0,
        'total_laboratorios': 0,
        'total_asignados': 0,
        'total_mantenimientos': 0,
        'equipos_recientes': [],
        'distribucion_aulas': [],
        'conic_gradient': 'conic-gradient(#9CA3AF 0% 100%)',
        'proximos_mantenimientos': []
    }
    if not conn:
        return stats
    
    try:
        with conn.cursor(as_dict=True) as cursor:
            # 1. Total de equipos
            cursor.execute("SELECT COUNT(*) AS total FROM equipos")
            row = cursor.fetchone()
            stats['total_equipos'] = row['total'] if row else 0
            
            # 2. Total de laboratorios (aulas)
            cursor.execute("SELECT COUNT(*) AS total FROM aulas")
            row = cursor.fetchone()
            stats['total_laboratorios'] = row['total'] if row else 0
            
            # 3. Total de asignados
            cursor.execute("SELECT COUNT(*) AS total FROM equipos WHERE estado = 'asignado'")
            row = cursor.fetchone()
            stats['total_asignados'] = row['total'] if row else 0
            
            # 4. Total de mantenimientos
            cursor.execute("SELECT COUNT(*) AS total FROM mantenimientos")
            row = cursor.fetchone()
            stats['total_mantenimientos'] = row['total'] if row else 0
            
            # 5. Equipos recientes
            query_equipos = """
            SELECT 
                e.id_equipo, 
                e.codigo_inventario, 
                a.nombre AS aula_nombre, 
                e.numero_banco, 
                CONCAT(r.nombre, ' ', r.apellido) AS responsable_nombre, 
                e.estado,
                m.fecha_mant AS ultimo_mant
            FROM equipos e
            LEFT JOIN aulas a ON e.id_aula = a.id_aula
            LEFT JOIN responsables r ON e.id_responsable = r.id_responsable
            LEFT JOIN (
                SELECT id_equipo, MAX(fecha_mant) AS fecha_mant
                FROM mantenimientos
                GROUP BY id_equipo
            ) m ON e.id_equipo = m.id_equipo
            ORDER BY e.fecha_ingreso DESC, e.id_equipo DESC;
            """
            cursor.execute(query_equipos)
            equipos_rows = cursor.fetchall()
            
            # Formatear fecha de último mantenimiento
            for eq in equipos_rows:
                if eq['ultimo_mant']:
                    eq['ultimo_mant_str'] = eq['ultimo_mant'].strftime('%d/%m/%Y')
                else:
                    eq['ultimo_mant_str'] = '-'
            stats['equipos_recientes'] = equipos_rows
            
            # 6. Distribución por aula (gráfico circular)
            query_dist = """
            SELECT 
                a.nombre AS aula_nombre, 
                COUNT(e.id_equipo) AS cantidad
            FROM equipos e
            LEFT JOIN aulas a ON e.id_aula = a.id_aula
            GROUP BY a.nombre
            ORDER BY cantidad DESC;
            """
            cursor.execute(query_dist)
            dist = cursor.fetchall()
            
            total_equipos = stats['total_equipos']
            if total_equipos > 0 and dist:
                colors = ['#1D4ED8', '#10B981', '#8B5CF6', '#F59E0B', '#EF4444', '#9CA3AF']
                bg_classes = ['bg-brand-accent', 'bg-green-500', 'bg-purple-500', 'bg-yellow-500', 'bg-red-500', 'bg-gray-400']
                
                gradient_parts = []
                current_percent = 0
                
                for i, d in enumerate(dist):
                    qty = d['cantidad']
                    pct = round((qty / total_equipos) * 100)
                    color = colors[i % len(colors)]
                    bg_class = bg_classes[i % len(bg_classes)]
                    
                    next_percent = current_percent + pct
                    if i == len(dist) - 1:
                        next_percent = 100
                    
                    gradient_parts.append(f"{color} {current_percent}% {next_percent}%")
                    
                    stats['distribucion_aulas'].append({
                        'aula_nombre': d['aula_nombre'] or 'Sin Aula',
                        'cantidad': qty,
                        'porcentaje': pct,
                        'bg_class': bg_class
                    })
                    
                    current_percent = next_percent
                
                if gradient_parts:
                    stats['conic_gradient'] = f"conic-gradient({', '.join(gradient_parts)})"
            else:
                stats['conic_gradient'] = "conic-gradient(#9CA3AF 0% 100%)"
                
            # 7. Próximos mantenimientos
            query_mants = """
            SELECT 
                m.id_equipo, 
                a.nombre AS aula_nombre, 
                e.numero_banco, 
                m.proximo_mant
            FROM mantenimientos m
            JOIN equipos e ON m.id_equipo = e.id_equipo
            LEFT JOIN aulas a ON e.id_aula = a.id_aula
            ORDER BY m.proximo_mant ASC;
            """
            cursor.execute(query_mants)
            mants_rows = cursor.fetchall()
            today = datetime.date.today()
            
            proximos = []
            for row in mants_rows:
                px_date = row['proximo_mant']
                if px_date:
                    diff_days = (px_date - today).days
                    if diff_days < 0:
                        dias_texto = f"Vencido hace {-diff_days} días"
                    elif diff_days == 0:
                        dias_texto = "Hoy"
                    else:
                        dias_texto = f"En {diff_days} días"
                        
                    proximos.append({
                        'id_equipo': row['id_equipo'],
                        'aula_nombre': row['aula_nombre'] or 'Sin Aula',
                        'numero_banco': row['numero_banco'] or '',
                        'proximo_mant': px_date.strftime('%d/%m/%Y'),
                        'dias_texto': dias_texto
                    })
            stats['proximos_mantenimientos'] = proximos
                
    except Exception as e:
        print(f"[SQL ERROR] Error fetching dashboard stats: {e}")
    finally:
        conn.close()
        
    return stats


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
    stats = get_dashboard_stats()
    return render_template('dashboard.html', stats=stats)


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


# ──────────────────────────────────────────────
# CRUD Componentes (MongoDB)
# ──────────────────────────────────────────────

@app.route('/componentes')
@login_required
@role_required('componentes')
def componentes():
    """Lista todos los equipos (hardware) de MongoDB con filtro opcional."""
    filtro = request.args.get('q', '').strip()
    equipos_hw = get_all_hardware(filtro if filtro else None)
    
    # Convertir ObjectId a string para evitar errores en template
    for eq in equipos_hw:
        if '_id' in eq:
            eq['_id'] = str(eq['_id'])
    
    return render_template('componentes.html', equipos=equipos_hw, filtro=filtro)


@app.route('/componentes/nuevo', methods=['GET', 'POST'])
@login_required
@role_required('componentes')
def componente_nuevo():
    """Formulario para agregar un nuevo equipo de hardware."""
    if request.method == 'POST':
        data = _parse_hardware_form(request.form)
        if not data.get('id_equipo'):
            flash('El ID del equipo es obligatorio.', 'error')
            return render_template('componente_form.html', equipo=data, modo='nuevo')
        
        if insert_hardware(data):
            flash(f'Equipo "{data["id_equipo"]}" creado exitosamente.', 'success')
            return redirect(url_for('componentes'))
        else:
            flash('Error al crear el equipo. Es posible que el ID ya exista.', 'error')
            return render_template('componente_form.html', equipo=data, modo='nuevo')
    
    return render_template('componente_form.html', equipo=None, modo='nuevo')


@app.route('/componentes/<id_equipo>')
@login_required
@role_required('componentes')
def componente_detalle(id_equipo):
    """Vista de detalle de un equipo con todos sus componentes."""
    equipo = get_hardware_by_id(id_equipo)
    if not equipo:
        flash('Equipo no encontrado.', 'error')
        return redirect(url_for('componentes'))
    
    if '_id' in equipo:
        equipo['_id'] = str(equipo['_id'])
    
    return render_template('componente_detalle.html', equipo=equipo)


@app.route('/componentes/<id_equipo>/editar', methods=['GET', 'POST'])
@login_required
@role_required('componentes')
def componente_editar(id_equipo):
    """Formulario para editar un equipo de hardware existente."""
    if request.method == 'POST':
        data = _parse_hardware_form(request.form)
        
        if update_hardware(id_equipo, data):
            flash(f'Equipo "{id_equipo}" actualizado exitosamente.', 'success')
            return redirect(url_for('componente_detalle', id_equipo=id_equipo))
        else:
            flash('Error al actualizar el equipo.', 'error')
            return render_template('componente_form.html', equipo=data, modo='editar', id_equipo=id_equipo)
    
    equipo = get_hardware_by_id(id_equipo)
    if not equipo:
        flash('Equipo no encontrado.', 'error')
        return redirect(url_for('componentes'))
    
    if '_id' in equipo:
        equipo['_id'] = str(equipo['_id'])
    
    return render_template('componente_form.html', equipo=equipo, modo='editar', id_equipo=id_equipo)


@app.route('/componentes/<id_equipo>/eliminar', methods=['POST'])
@login_required
@role_required('componentes')
def componente_eliminar(id_equipo):
    """Elimina un equipo de hardware de MongoDB."""
    if delete_hardware(id_equipo):
        flash(f'Equipo "{id_equipo}" eliminado exitosamente.', 'success')
    else:
        flash('Error al eliminar el equipo.', 'error')
    return redirect(url_for('componentes'))


def _parse_hardware_form(form):
    """Parsea los datos del formulario HTML a un diccionario compatible con MongoDB."""
    data = {
        'id_equipo': form.get('id_equipo', '').strip(),
        'fabricante': form.get('fabricante', '').strip(),
        'modelo': form.get('modelo', '').strip(),
        'tipo': form.get('tipo', 'desktop').strip(),
        'cpu': {
            'marca': form.get('cpu_marca', '').strip(),
            'modelo': form.get('cpu_modelo', '').strip(),
            'nucleos': int(form.get('cpu_nucleos', 0) or 0),
            'frecuencia_ghz': float(form.get('cpu_frecuencia', 0) or 0),
        },
        'ram': {
            'cantidad_gb': int(form.get('ram_cantidad', 0) or 0),
            'tipo': form.get('ram_tipo', '').strip(),
            'frecuencia_mhz': int(form.get('ram_frecuencia', 0) or 0),
        },
        'discos': [],
        'sistema_operativo': {
            'nombre': form.get('so_nombre', '').strip(),
            'version': form.get('so_version', '').strip(),
        },
        'perifericos': {
            'monitor': form.get('periferico_monitor', '').strip(),
            'teclado': form.get('periferico_teclado', '').strip(),
            'mouse': form.get('periferico_mouse', '').strip(),
        },
        'fecha_registro': datetime.datetime.utcnow(),
    }
    
    # Parsear discos dinámicos
    i = 0
    while True:
        disco_tipo = form.get(f'disco_{i}_tipo')
        if disco_tipo is None:
            break
        disco = {
            'tipo': disco_tipo.strip(),
            'interfaz': form.get(f'disco_{i}_interfaz', '').strip(),
            'capacidad_gb': int(form.get(f'disco_{i}_capacidad', 0) or 0),
            'marca': form.get(f'disco_{i}_marca', '').strip(),
        }
        if disco['tipo']:  # Solo agregar si tiene tipo
            data['discos'].append(disco)
        i += 1
    
    return data


# --- Stubs para enlaces del sidebar ---

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
    mongo_ok = test_mongo_connection()
    all_ok = db_ok and mongo_ok
    status = 200 if all_ok else 503
    return {
        "status": "ok" if all_ok else "degraded",
        "sql_server": "connected" if db_ok else "disconnected",
        "mongodb": "connected" if mongo_ok else "disconnected",
        "auth_mode": config.AUTH_MODE
    }, status


# ── Manejo de errores ──────────────────────
@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
