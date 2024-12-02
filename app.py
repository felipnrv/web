from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import os
import hashlib
import db

# Configuración del template folder
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

app = Flask(__name__, template_folder=template_dir)
app.secret_key = 'your_secret_key'



# Página principal: muestra proyectos, tareas y comentarios
@app.route('/')
def home():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para acceder a esta página.', 'warning')
        return redirect(url_for('login'))

    cursor = db.database.cursor()

    # Obtener todos los proyectos
    cursor.execute("SELECT * FROM projects")
    projects = cursor.fetchall()
    project_list = []
    column_names = [column[0] for column in cursor.description]
    for record in projects:
        project_list.append(dict(zip(column_names, record)))

    # Crear un diccionario de proyectos para buscar por ID
    project_dict = {project['id']: project['name'] for project in project_list}

    # Obtener todas las tareas
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()
    task_list = []
    column_names = [column[0] for column in cursor.description]
    for record in tasks:
        task = dict(zip(column_names, record))
        # Añadir el nombre del proyecto a cada tarea
        task['project_name'] = project_dict.get(task['project_id'], 'Sin proyecto')
        task_list.append(task)

    # Obtener todos los comentarios
    cursor.execute("SELECT * FROM comments")
    comments = cursor.fetchall()
    comment_list = []
    column_names = [column[0] for column in cursor.description]
    for record in comments:
        comment_list.append(dict(zip(column_names, record)))

    cursor.close()

    current_user = {'id': session['user_id'], 'username': session['username']}
    return render_template(
        'index.html', 
        projects=project_list, 
        tasks=task_list, 
        comments=comment_list, 
        current_user=current_user
    )



# Registro de usuarios
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()  # Encriptar contraseña

        cursor = db.database.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user:
            flash('El correo ya está registrado. Por favor, usa otro.', 'danger')
            return redirect(url_for('register'))

        # Insertar nuevo usuario
        sql = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
        data = (username, email, hashed_password)
        cursor.execute(sql, data)
        db.database.commit()
        cursor.close()

        flash('Usuario registrado exitosamente. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()  # Encriptar contraseña

        cursor = db.database.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, hashed_password))
        user = cursor.fetchone()
        cursor.close()

        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('Inicio de sesión exitoso.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Credenciales incorrectas. Inténtalo de nuevo.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

# Cerrar sesión
@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('login'))



@app.route('/project', methods=['POST'])
def add_or_edit_project():
    project_id = request.form.get('id')  # Obtener el ID si existe
    name = request.form['name']
    description = request.form.get('description', '')

    cursor = db.database.cursor()

    if project_id:  # Si hay un ID, actualizamos el proyecto
        sql = "UPDATE projects SET name = %s, description = %s WHERE id = %s"
        cursor.execute(sql, (name, description, project_id))
        flash('Proyecto actualizado correctamente.', 'success')
    else:  # Si no hay ID, creamos un nuevo proyecto
        sql = "INSERT INTO projects (name, description) VALUES (%s, %s)"
        cursor.execute(sql, (name, description))
        flash('Proyecto creado correctamente.', 'success')

    db.database.commit()
    cursor.close()

    return redirect(url_for('home'))





@app.route('/task', methods=['POST'])
def add_or_edit_task():
    task_id = request.form.get('id')  # Obtener ID de la tarea si existe
    title = request.form['title']
    description = request.form.get('description', '')
    project_id = request.form['project_id']

    cursor = db.database.cursor()

    if task_id:  # Si hay un ID, actualizar la tarea
        sql = "UPDATE tasks SET title = %s, description = %s, project_id = %s WHERE id = %s"
        cursor.execute(sql, (title, description, project_id, task_id))
        flash('Tarea actualizada correctamente.', 'success')
    else:  # Si no hay ID, crear una nueva tarea
        sql = "INSERT INTO tasks (title, description, project_id) VALUES (%s, %s, %s)"
        cursor.execute(sql, (title, description, project_id))
        flash('Tarea creada correctamente.', 'success')

    db.database.commit()
    cursor.close()

    return redirect(url_for('home'))

@app.route('/delete_task/<int:id>', methods=['GET'])
def delete_task(id):
    cursor = db.database.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = %s", (id,))
    db.database.commit()
    cursor.close()
    flash('Tarea eliminada correctamente.', 'success')
    return redirect(url_for('home'))


@app.route('/delete_project/<int:id>', methods=['GET'])
def delete_project(id):
    cursor = db.database.cursor()
    cursor.execute("DELETE FROM projects WHERE id = %s", (id,))
    db.database.commit()
    cursor.close()
    flash('Proyecto eliminado correctamente.', 'success')
    return redirect(url_for('home'))


# Agregar comentario
@app.route('/comment', methods=['POST'])
def add_or_edit_comment():
    comment_id = request.form.get('id')  # Obtener ID del comentario si existe
    content = request.form['content']
    task_id = request.form['task_id']
    user_id = session['user_id']  # Usuario actual

    cursor = db.database.cursor()

    if comment_id:  # Si hay un ID, actualizar el comentario
        sql = "UPDATE comments SET content = %s, task_id = %s WHERE id = %s"
        cursor.execute(sql, (content, task_id, comment_id))
        flash('Comentario actualizado correctamente.', 'success')
    else:  # Si no hay ID, crear un nuevo comentario
        sql = "INSERT INTO comments (content, task_id, user_id) VALUES (%s, %s, %s)"
        cursor.execute(sql, (content, task_id, user_id))
        flash('Comentario creado correctamente.', 'success')

    db.database.commit()
    cursor.close()

    return redirect(url_for('home'))


@app.route('/delete_comment/<int:id>', methods=['GET'])
def delete_comment(id):
    cursor = db.database.cursor()
    cursor.execute("DELETE FROM comments WHERE id = %s", (id,))
    db.database.commit()
    cursor.close()
    flash('Comentario eliminado correctamente.', 'success')
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True, port=4000)
