from flask import Flask, session, render_template, request, redirect, url_for, flash, jsonify, json, abort, send_file
from flask_mysqldb import MySQL
from sqlalchemy import tuple_
from PIL import Image
from io import BytesIO

from sqlalchemy import tuple_
from wtforms import SelectField
from flask_wtf import FlaskForm
from email.message import EmailMessage
import ssl
import pyotp
import qrcode

from cmath import pi
from pickle import NONE
import numpy as np
import math
import smtplib
from config import Config
from datetime import datetime, timedelta
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from Auth import Auth
from Auth import Company
from dotenv import load_dotenv
import os


# Variables Globales
dataqryCtxt = ""
load_dotenv()

app = Flask(__name__)

# MySQL Connection :
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

strConnection = "mysql://{user}:{pwd}@{host}/{db}".format(user = os.getenv('MYSQL_USER'), pwd = os.getenv('MYSQL_PASSWORD'), host = os.getenv('MYSQL_HOST'), db = os.getenv('MYSQL_DB'))

print (strConnection)

auth = Auth(strConnection)

# Settings
app.secret_key = 'mysecretkeyJAPSNP'

# Configuración de la duración de la sesión
app.permanent_session_lifetime = timedelta(minutes=30)  # Aquí defines 30 minutos de duración de la sesión

# Cookies :
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # o 'Strict'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'signja'

@login_manager.user_loader
def load_user(user_id):
    return auth.get_user_by_id(user_id)

@app.before_request
def before_request_func():
    print('before request')
    if (current_user != None and hasattr(current_user, 'id')):        
        print('changing tenant')
        tenant = auth.get_tenant(current_user.id)
        app.config['MYSQL_DB'] = tenant
        #app.config['MYSQL_USER'] = observusu
        #app.config['MYSQL_PASSWORD'] = elpasspaMys
        print(tenant)

@app.route('/')
def Index():
    return render_template('index.html')

@app.route('/signja')
def signja():
    return render_template('login.html')

def update_session_id_in_db(username, session_id):
    # Conectar a la base de datos
    curUs = mysql.connection.cursor()
    
    # Ejecutar la actualización del session_id para el usuario dado
    curUs.execute("UPDATE usuarios SET session_id = %s WHERE email_usu = %s", (session_id, username))
    
    # Confirmar la transacción
    mysql.connection.commit()
    
    # Cerrar el cursor
    curUs.close()

@app.route('/login2fa', methods=['POST'])
def login2fa():
    
    if request.method == 'POST':        
        email = request.values['InputEmail']
        password = request.values['InputPassword']

        try:
            user = auth.get_user(email)

            if user.check_password(password):
                login_user(user)
                if user.is_2fa_enabled:
                    return redirect('verify_2fa')
                else:
                    return redirect('enable_2fa')
        except Exception as e:
            error = 'Credenciales Inválidas'
            return render_template('login.html', errorj=error, vusername=email)

    # Si no se cumple ninguna de las condiciones anteriores
    error = 'Credenciales Inválidas'
    return render_template('pages-sign-in.html', errorj=error, vusername=email)
        
def get_session_id_from_db(username):
    # Conectar a la base de datos
    curGs = mysql.connection.cursor()
    
    # Ejecutar la consulta para obtener el session_id del usuario
    curGs.execute("SELECT session_id FROM usuarios WHERE email_usu = %s", [username])
    
    # Obtener el resultado de la consulta
    result = curGs.fetchone()
    
    # Cerrar el cursor
    curGs.close()
    
    # Si se encuentra el resultado, devolver el session_id, de lo contrario devolver None
    if result:
        return result[0]  # result puede ser un diccionario si configuras el cursor con MySQLdb o pymysql
    return None

@app.route('/enable_2fa')
def enable_2fa():
    # Generar clave secreta única
    secret = pyotp.random_base32()

    # Obtener el nombre de usuario del usuario autenticado
    username = session.get('username')

    # Guardar la clave secreta en la base de datos    
    cur2falog = mysql.connection.cursor()
    cur2falog.execute( "UPDATE usuarios SET secret_key = %s, is_2fa_enabled = %s WHERE email_usu = %s", (secret, 1, username) )
    # Confirmar los cambios en la base de datos
    mysql.connection.commit()

    # Generar una URL para Google Authenticator
    totp = pyotp.TOTP(secret)
    otp_url = totp.provisioning_uri(username, issuer_name="SINAPSIS V 2.0")    

    # Generar código QR para que el usuario lo escanee con Google Authenticator
    img = qrcode.make(otp_url)
    img.save(f"static/{username}_qrcode.png")

    return render_template('enable_2fa.html', qrcode=f"{username}_qrcode.png")

@app.route('/verify_2fa', methods=['POST', 'GET'])
def verify_2fa():
    if request.method == 'POST':
        token = request.form['token']
        username = session.get('username')
        print(current_user)
        if (current_user.check_2FA(token)):
            return redirect('/inicio')
            #return redirect('/logearse')

    return render_template('verify_2fa.html')

@app.route('/disable_2fa')
def disable_2fa():
    username = session.get('username')
    cur2fadis = mysql.connection.cursor()
    cur2fadis.execute("UPDATE usuarios SET is_2fa_enabled = %s, secret_key = %s WHERE email_usu = %s", (False, 0, username))
    data2fadis = cur2fadis.fetchall()
    return redirect('/signj')

@app.route('/avatar', methods=['GET'])
def avatar():
    if (current_user != None and hasattr(current_user, 'avatar')):
        
        return send_file(
            io.BytesIO(current_user.avatar),
            mimetype='image/jpeg',
            as_attachment=True,
            download_name='%s.jpg' % current_user.id)
    
    abort(404)

@app.route('/logearse', methods=['GET'])
def logearse():
    errorj = None
    if request.method == 'GET':
        vusername = session.get('username')
        
        #vusername = request.values['InputEmail']
        #vpasswduser = request.values['InputPassword']

        curusuarios = mysql.connection.cursor()
        curusuarios.execute( "SELECT * FROM usuarios WHERE email_usu LIKE %s", [vusername] )
        datausuarios = curusuarios.fetchall()
        curusuarios = datausuarios

        if not datausuarios:
            flash('Error de login !!!', 'error')
            errorj = 'Credenciales Inválidas'
            return render_template('login.html', errorj=errorj, vusername=vusername)        

        vpasswduser = datausuarios[0][10]
        session['vpasswduser'] = vpasswduser
        
        curpasswd = mysql.connection.cursor()
        curpasswd.execute( "SELECT * FROM Usuarios WHERE passwd_usu LIKE %s AND email_usu LIKE %s", (vpasswduser,vusername))
        datapsswus = curpasswd.fetchall()
        triplehp = datapsswus

        if not datapsswus:
            flash('Error de login !!!', 'error')
            errorj = 'Credenciales Inválidas'
            return render_template('login.html', errorj=errorj, vusername=vusername)

        global observusu
        global elcorr
                        
        laciud = triplehp[0][9]
        observusu = triplehp[0][13]
        elcorr = triplehp[0][7]
        codUIchamp = triplehp[0][2]
        TipodU = triplehp[0][1]
        nomdlus = triplehp[0][3]
        nicknu = triplehp[0][13]            
        app.config['emprusu'] = str(triplehp[0][14])

        # Procesamiento de avatar
        avatr = triplehp[0][12]
        nomavtr = triplehp[0][15]
        #avatr1 = Image.open(BytesIO(avatr))
        #avatr1.save('static/img/avatars/'+nomavtr)
        #avatr1.close()

        # Inicio de Sesión:
        session['TipodU'] = TipodU
        session.permanent = True
        session.modified = True
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Convertir a string
        if 'last_activity' in session:
            last_activity = datetime.strptime(session['last_activity'], '%Y-%m-%d %H:%M:%S')
            if (datetime.now() - last_activity).total_seconds() > app.permanent_session_lifetime.total_seconds():
                session.pop('username', None)
                flash('Sesión expirada por inactividad', 'warning')
                return redirect(url_for('signj'))
        session['last_activity'] = now  # Guardar como string
        flash('Login successful!')
        
        global labdempr, nomemp

        # Procesamiento de la empresa y otros datos

        emprusu = app.config['emprusu']        

        curempr = mysql.connection.cursor()
        curempr.execute( "SELECT basedd_emp FROM empresas where codemp_emp LIKE %s", (emprusu))
        dataempr = curempr.fetchall()
        labdempr = dataempr[0][0]
        #print(labdempr)
        
        curempr1 = mysql.connection.cursor()
        curempr1.execute( "SELECT * FROM empresas where codemp_emp LIKE %s", (emprusu))
        dataempr1 = curempr1.fetchall()
        nomemp = dataempr1[0][1]
        #print(nomemp)
        nomdashb = dataempr1[0][26]

        app.config['MYSQL_HOST'] = 'localhost'
        app.config['MYSQL_USER'] = 'root'
        app.config['MYSQL_PASSWORD'] = 'Sire5997_2024*.'
        app.config['MYSQL_DB'] = labdempr
        #mysql1 = MySQL(app)

        #curpaciud = mysql.connection.cursor()
        #curpaciud.execute("SELECT nom_ciud FROM Ciudades WHERE cod_ciud LIKE %s", [laciud])
        #datapaciud = curpaciud.fetchall()
        #nomciud = datapaciud[0]

        #curciuds = mysql.connection.cursor()
        #curciuds.execute("SELECT * FROM Ciudades ORDER BY nom_ciud")
        #dataciuds = curciuds.fetchall()
        #ciuds = dataciuds  

        #  3) Desabilitar la navegación CON LA FLECHA hacia atrás, ver index en SIRE.

        # Redirecciona o renderiza según sea necesario

        #  3) Desabilitar la navegación CON LA FLECHA hacia atrás, ver index en SIRE.

        # Redirecciona o renderiza según sea necesario        
        
        if TipodU in [4, 5]:            
            flash('Bienvenido !!! ' + vusername )
            print('Bienvenido !!! ', vusername)
            return render_template('misdatos2.html', datosuser=datapsswus, cchampUI = codUIchamp)
        
        elif TipodU in [1, 2, 3]:
                
            flash('Bienvenido !!! ' + vusername )
            print('Bienvenido !!! ', vusername)
            #nomdashbreturn render_template('dash_default_3THTB.html', datosuser=datapsswus, cchampUI = codUIchamp, 
            return render_template(nomdashb, datosuser=datapsswus, cchampUI = codUIchamp, 
            elnomdu = nomdlus, apodou = nicknu, elavatar = avatr,
            nickn=observusu, emlusr=elcorr, nombredle=nomemp )
                
        else:
            flash('Error de login !!!', 'error')
            print('Error de login !!!')
            errorj = 'Credenciales Inválidas'
            return render_template('login.html', errorj=errorj, vusername=vusername, datosuser=datapsswus)

    # Si en el método no se cumple ninguna condición
    return render_template('login.html', errorj=errorj)

@app.route('/inicio')
def inicio():    
    return render_template('dash_default_3THTA.html')

@app.route('/intro')
def intro():
    return render_template('form-summernote.html')

@app.route('/dashppal')
def dashppal():
     return render_template('form-advanced.html')

@app.route('/exit')
def exit():
    session.pop('username',None)
    session.clear()    
    exit
    return render_template('index.html')

## JOTALEJO SW Y SISTEMAS ;) - FUNCIONES RECURSIVAS  ==>

# ==> PARA GRABACIÓN Y MODIFICACIÓN DE DATOS PYTHON

def sanitize_input(value):
    """Sanitize input to avoid SQL injection and replace problematic characters."""
    if isinstance(value, str):
        return value.replace("'", ".")
    return value  # Devuelve el valor original si no es una cadena

def get_code_from_db(value, lookup_table, lookup_field, return_field, cursor):
    """Get a code from the database based on a value and lookup fields."""
    query = f"SELECT {return_field} FROM {lookup_table} WHERE {lookup_field} = %s"
    cursor.execute(query, (value,))
    result = cursor.fetchone()
    if result:
        return result[0]  # Accede al primer valor de la tupla
    return None

def recursive_data_grabber(fields_html, fields_db, lookup_info, cursor):
    """Recursively grab data from form and perform lookups if necessary."""
    data = {}
    for html_field, db_field in zip(fields_html, fields_db):
        value = request.form.get(html_field) or request.values.get(html_field, "")

        # Check if lookup_info is provided and this field requires a database lookup
        if lookup_info and db_field in lookup_info:
            lookup_table, lookup_field, return_field = lookup_info[db_field]
            value = get_code_from_db(value, lookup_table, lookup_field, return_field, cursor)
        
        data[db_field] = sanitize_input(value)
    return data

def insert_into_mysql(table, data, cursor):
    """Insert the grabbed data into MySQL table using an existing cursor."""
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    values = tuple(data.values())

    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    cursor.execute(query, values)
    
# FIN FUNCIONES RECURSIVAS

###  ACA COMIENZA EL CONTROL DE LOS FORMULARIOS DE SINAPSIS V. 2.0

# >> FORMULARIO INTEGRAL I : Direccionamiento Estratégico

#  Principal de Captura :
@app.route('/plandes')
def plandes():

    id = session.get('emprusu')

    # Instanciar la clase Company
    company_instance = Company()

    # Verificar el ID de la empresa usando el método check_idempr
    # Reemplaza `id` con el valor que obtengas del contexto de la aplicación
#    emprusu1 = company_instance.check_idempr(id)

    curempr1 = mysql.connection.cursor()
    #curempr1.execute( "SELECT * FROM empresas where codemp_emp = %s", (emprusu1,))
    curempr1.execute( "SELECT * FROM empresas where codemp_emp = 4" )
    dataempr1 = curempr1.fetchall()
    curempr1.close()
    nickn1=dataempr1[0][28]

    curvlrs = mysql.connection.cursor()
    curvlrs.execute("SELECT * FROM valores")
    datavlrs = curvlrs.fetchall()
    curvlrs.close()
    vers = datavlrs[0][0]
    print(vers)

    curDest = mysql.connection.cursor()
    curDest.execute('SELECT * FROM direccestrat')
    dataDest = curDest.fetchall()
    curDest.close()

    return render_template('form-plandes.html', nickn=nickn1, losva=datavlrs, eldire=dataDest)

#  Adicionar Misión y Visión:
@app.route('/Add_direst', methods=['POST'])
def Add_direst():
    if request.method == 'POST':
        # Example fields: HTML field names and corresponding DB field names
        fields_html = ['fecdirest','mision', 'vision']  # HTML form field names

        # Example fields: HTML field names and corresponding DB field names
        fields_db = ['fec_direst','misi_direst', 'visi_direst']  # DB table field names
        table_name = 'direccestrat'  # Name of your table

        cursorJAP = mysql.connection.cursor()
        data = recursive_data_grabber(fields_html, fields_db, lookup_info=None, cursor=cursorJAP)

        data['codemp_direst'] = app.config['emprusu']
        
        # Assuming cursor is already available
       
        insert_into_mysql(table_name, data, cursorJAP)
        mysql.connection.commit()
        flash('Mision, Visión agregadas')
        return redirect(url_for('plandes'))

#  Adicionar Valores:
@app.route('/Add_valores', methods=['POST'])
def Add_valores():
    if request.method == 'POST':
        # Example fields: HTML field names and corresponding DB field names
        fields_html = ['titv', 'descv']  # HTML form field names

        # Example fields: HTML field names and corresponding DB field names
        fields_db = ['tit_val', 'desc_val']  # DB table field names
        table_name = 'valores'  # Name of your table

        cursorJAP = mysql.connection.cursor()
        data = recursive_data_grabber(fields_html, fields_db, lookup_info=None, cursor=cursorJAP)

        data['codemp_val'] = app.config['emprusu']
        
        # Assuming cursor is already available
       
        insert_into_mysql(table_name, data, cursorJAP)
        mysql.connection.commit()
        flash('Valor Agregado')
        return redirect(url_for('plandes'))
    
#  Borrar :
@app.route('/Delete_val/<string:id>')
def Delete_val(id):
    curDlosVal = mysql.connection.cursor()
    curDlosVal.execute('DELETE FROM valores WHERE cod_val = {0}'.format(id))
    mysql.connection.commit()
    flash('Valor Eliminado Satisfactoriamente')
    return redirect(url_for('plandes'))

#  Editar :
## Se hace directamente en la página, mediante un modal

#  Actualizar :
@app.route('/Update_val', methods=['POST'])
def Update_val():
    if request.method == 'POST':
        vmtitval = request.form['titv']
        vmdescv = request.form['descv']
        vid = request.form['id']

        curActlosV = mysql.connection.cursor()
        curActlosV.execute("""
            UPDATE valores
            SET tit_val = %s,
                desc_val = %s
            WHERE cod_val = %s
        """, (vmtitval, vmdescv, vid))
        mysql.connection.commit()
        flash('Modificación realizada con éxito')

        return redirect(url_for('plandes'))

# >> FINAL FORMULARIO INTEGRAL I : Direccionamiento Estratégico

# >> FORMULARIO II : Perspectiva Financiera

#  Principal de Captura :
@app.route('/creasol')
def creasol():
            
    curlosTes = mysql.connection.cursor()
    curlosTes.execute("SELECT * FROM estrategiatipos")
    datalosTes = curlosTes.fetchall()

    # Obtener el ID de la empresa desde la sesión
    company_id = session.get('emprusu')

    id = session.get('emprusu')

    # Instanciar la clase Company
    company_instance = Company()

    # Verificar el ID de la empresa usando el método check_idempr
    # Reemplaza `id` con el valor que obtengas del contexto de la aplicación
    #emprusu1 = company_instance.check_idempr(id)
    #print('Hola acá es :')
    #print(emprusu1)

    curempr1 = mysql.connection.cursor()
    curempr1.execute( "SELECT * FROM empresas where codemp_emp LIKE 4")
    dataempr1 = curempr1.fetchall()
    nickn1=dataempr1[0][28]

    # Crear una instancia de SQLAlchemy Session
    #with session(engine) as db_session:
        # Crear una instancia de Company
        #company_instance = Company()

        # Llamar al método check_idempr
        #company = company_instance.check_idempr(company_id, db_session)

        # Verificar si se encontró la empresa
        #if not company:
        #    return "Empresa no encontrada", 404

        # Obtener el nickname
        #nickn1 = company.nname
    
    curpers = mysql.connection.cursor()
    curpers.execute('SELECT * FROM perspectivas')
    datapers = curpers.fetchall()

    curpers = mysql.connection.cursor()
    curpers.execute("""
        SELECT cod_pers, objet_pers, meta_pers, estrat_pers, nom_estrtip FROM perspectivas
        JOIN estrategiatipos ON cod_estrtip = codestrat_pers
    """)
    datapers = curpers.fetchall()

    return render_template('form-creasol.html', Tipest=datalosTes, laspersp=datapers, nickn=nickn1 )

# Adicionar Perspectiva:
@app.route('/Add_persfin', methods=['POST'])
def Add_persfin():
    if request.method == 'POST':
        # Example fields: HTML field names and corresponding DB field names        
        fields_html = ['descO', 'metaO', 'estO', 'tipoestr']  # HTML form field names
        fields_db = ['objet_pers', 'meta_pers', 'estrat_pers', 'codestrat_pers']  # DB table field names
        table_name = 'perspectivas'  # Name of your table

        # Define lookup information: {db_field: (lookup_table, lookup_field, return_field)}
        lookup_info = {
            'codestrat_pers': ('estrategiatipos', 'nom_estrtip', 'cod_estrtip')
        }

        cursorJAP = mysql.connection.cursor()
        data = recursive_data_grabber(fields_html, fields_db, lookup_info, cursorJAP)
        data['codemp_pers'] = app.config['emprusu']

        # Determine the value for codpptip_pers based on perspective type
        perspective_type = request.form.get('perspective_type', '').lower()
        if perspective_type == 'financiera':
            data['codpptip_pers'] = 1
        elif perspective_type == 'clientes':
            data['codpptip_pers'] = 2
        else:
            data['codpptip_pers'] = None  # Or handle other cases as needed
        
        insert_into_mysql(table_name, data, cursorJAP)
        mysql.connection.commit()
        flash('Perspectiva Agregada')
        return redirect(url_for('creasol'))
    
#  Borrar :
@app.route('/Delete_pers/<string:id>')
def Delete_pers(id):
    curDlosVal = mysql.connection.cursor()
    curDlosVal.execute('DELETE FROM perspectivas WHERE cod_pers = {0}'.format(id))
    mysql.connection.commit()
    flash('Perspectiva Eliminada Satisfactoriamente')
    return redirect(url_for('creasol'))

#  Editar :
## Se hace directamente en la página, mediante un modal

#  Actualizar :
@app.route('/Update_pers', methods=['POST'])
def Update_pers():
    if request.method == 'POST':
        vdescO = request.form['descO']
        vmetaO = request.form['metaO']
        vestO = request.form['estO']                
        
        vtipoestr=""
        datatipoestr = ""
        try:
            vtipoestr = request.values['tipoestr']
            curtipoestr = mysql.connection.cursor()
            curtipoestr.execute( "SELECT cod_estrtip FROM estrategiatipos WHERE nom_estrtip LIKE %s", [vtipoestr] )
            datatipoestr = curtipoestr.fetchall()
            dtipoestr=datatipoestr[0]
        except:
            vtipoestr=""

        vid = request.form['id']

        curActlosP = mysql.connection.cursor()
        curActlosP.execute("""
            UPDATE perspectivas
            SET objet_pers = %s,
                meta_pers = %s,
                estrat_pers = %s,
                codestrat_pers = %s
            WHERE cod_pers = %s
        """, (vdescO, vmetaO, vestO, dtipoestr, vid))
        mysql.connection.commit()
        flash('Modificación realizada con éxito')

        return redirect(url_for('creasol'))
    
# >> FINAL FORMULARIO II : Perspectiva Financiera

# >> FORMULARIO III : Proyectos - Cronograma

#  Principal de Captura :
@app.route('/proyectos')
def proyectos():
            
    id = session.get('emprusu')

    # Instanciar la clase Company
    company_instance = Company()

    # Verificar el ID de la empresa usando el método check_idempr
    # Reemplaza `id` con el valor que obtengas del contexto de la aplicación
    emprusu1 = company_instance.check_idempr(id)

    curempr1 = mysql.connection.cursor()
    curempr1.execute( "SELECT * FROM empresas where codemp_emp LIKE %s", (emprusu1,))
    dataempr1 = curempr1.fetchall()
    nickn1=dataempr1[0][28]

    return render_template('form-proyectos.html', nickn=nickn1 )

# >> FINAL FORMULARIO III : Proyectos - Cronograma

@app.route('/add_DatBas', methods=['POST'])
def add_DatBas():
    if request.method == 'POST':

        vfechsoli = request.form['fechsoli']
        vhradsolicit = request.form['hradsolicit']
        vnradic = request.form['nradic']
        vcrglos = request.values['crglos']
        vlaCant = request.form['laCant']

        # Acá tratamos de leer el nuevo nombre del cargo
        #  de tal manera que hagamos un insert posterior 
        #  en caso que exista un dato
        try:
            vnomCrg = request.values['nomCrg']
        except:
            vnomCrg = ""
        else:
            vnomCrg = request.values['nomCrg']

        # Manejo del Área que requiere :
            
        # Gerencial
        vaqreGer=""
        try:
            vaqreGer = request.form['aqreGer']
            #print(vaqreGer)
        except:
            vaqreGer=""
        else:
            vaqreGer = request.form['aqreGer']

        # Administrativo
        vaqreAdt=""
        try:
            vaqreAdt = request.form['aqreAdt']
            #print(vaqreAdt)
        except:
            vaqreAdt=""
        else:
            vaqreAdt = request.form['aqreAdt']

        # Operativo
        vaqreOper=""
        try:
            vaqreOper = request.form['aqreOper']
            #print(vaqreOper)
        except:
            vaqreOper=""
        else:
            vaqreOper = request.form['aqreOper']

        # Manejo del Género :
        # Masculino
        vmale=""
        try:
            vmale = request.form['male']
            #print(vmale)
        except:
            vmale=""
        else:
            vmale = request.form['male']

        # Femenino
        vfemale=""
        try:
            vfemale = request.form['female']
            #print(vfemale)
        except:
            vfemale=""
        else:
            vfemale = request.form['female']

        # Indiferente
        vindif=""
        try:
            vindif = request.form['indif']
            #print(vindif)
        except:
            vindif=""
        else:
            vindif = request.form['indif']

        

        vmedicprob = vmedicprob[0:1]
        vmedicimpac = vmedicimpac[0:1]
        vmedcombina = vmedicprob + vmedicimpac

        vmedicodg = request.form['medicodg']
        curAdmediden = mysql.connection.cursor()
        curAdmediden.execute("SELECT cod_iden FROM identificacion WHERE codgen_iden LIKE %s", [vmedicodg])
        datAdmediden = curAdmediden.fetchall()
        codIdenM = datAdmediden[0]

        curAdmedcomb = mysql.connection.cursor()
        curAdmedcomb.execute("SELECT codcomb_comb FROM combinaciones WHERE pondri_comb LIKE %s", [vmedcombina])
        dataAdmedcomb = curAdmedcomb.fetchall()
        codCombM = dataAdmedcomb[0]

        curAgrMedic = mysql.connection.cursor()
        curAgrMedic.execute("""
        INSERT INTO medicion (codiden_med, codcomb_med)
        VALUES (%s, %s)
        """, (codIdenM, codCombM))
        mysql.connection.commit()

        flash('Riesgo Medido !!!')
        return redirect(url_for('medic'))

if __name__ == '__main__':
    app.run(port=3003, debug=True)

# This is just a dummy database of users and passwords, in a real app you would use a secure database
users = {'user1': 'password1', 'user2': 'password2'}

# This is the login route, which will display the login form and handle the form submission
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            # The user has successfully authenticated, so redirect them to the home page
            return redirect(url_for('home'))
        else:
            # The user entered an incorrect username or password, so display an error message
            error = 'Invalid username or password'
            return render_template('login.html', error=error)
    else:
        # The user is just arriving at the login page, so display the login form
        return render_template('login.html')

# This is the home page route, which requires the user to be authenticated
@app.route('/')
def home():
    # Check if the user is authenticated
    if 'username' in session:
        return render_template('home.html', username=session['username'])
    else:
        # If the user is not authenticated, redirect them to the login page
        return redirect(url_for('login'))

# This route will log the user out by removing their username from the session
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))