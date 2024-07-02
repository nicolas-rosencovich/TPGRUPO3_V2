from flask_cors import CORS 

from flask import Flask, request, jsonify

import mysql.connector

from werkzeug.utils import secure_filename

import os

import time

app = Flask(__name__)
CORS(app)


class Catalogo:

    def __init__(self, host, user, password, database):
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password= password
        )
        self.cursor = self.conn.cursor()

        try:
            self.cursor.execute(f"USE {database}")
        except mysql.connector.Error as err:
            if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                self.cursor.execute(f"CREATE DATABASE {database}")
                self.conn.database = database
            else:
                raise err

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS socios (
                            codigo INT AUTO_INCREMENT PRIMARY KEY,
                            documento INT (8) NOT NULL,
                            nombre VARCHAR (50) NOT NULL,
                            telefono INT (11) NOT NULL,
                            mail VARCHAR (30),
                            direccion VARCHAR (100),
                            foto_url VARCHAR(255))''')
        self.conn.commit()

        self.cursor.close()
        self.cursor = self.conn.cursor(dictionary=True)

    def agregar_socio(self, documento, nombre, telefono, mail, direccion, foto):

        sql = "INSERT INTO socios (documento, nombre, telefono, mail, direccion, foto_url) VALUES (%s, %s, %s, %s, %s, %s)"
        valores = (documento, nombre, telefono, mail, direccion, foto)

        self.cursor.execute(sql, valores)
        self.conn.commit()
        return self.cursor.lastrowid

    def consultar_socio(self, codigo):
        self.cursor.execute(f"SELECT * FROM socios WHERE codigo = {codigo}")
        return self.cursor.fetchone()

    def modificar_socio(self, codigo, nuevo_documento, nuevo_nombre, nuevo_telefono, nuevo_mail, nueva_direccion, nueva_foto):
        sql = "UPDATE socios SET documento= %s, nombre = %s, telefono = %s, mail = %s, direccion = %s, foto_url = %s WHERE codigo = %s"
        valores = (nuevo_documento, nuevo_nombre, nuevo_telefono,
                   nuevo_mail, nueva_direccion, nueva_foto, codigo)
        self.cursor.execute(sql, valores)
        self.conn.commit()
        return self.cursor.rowcount > 0

    def mostrar_socio(self, codigo):
        socio = self.consultar_socio(codigo)
        if socio:
            print("*" * 50)
            print(f"Código...........: {socio['codigo']}")
            print(f"Documento........: {socio['documento']}")
            print(f"Nombre...........: {socio['nombre']}")
            print(f"Teléfono.........: {socio['telefono']}")
            print(f"Mail.............: {socio['mail']}")
            print(f"Dirección........: {socio['direccion']}")
            print(f"Foto.............: {socio['foto_url']}")
            print("*" * 50)
        else:
            print("Socio no encontrado.")

    def listar_socios(self):
        self.cursor.execute("SELECT * FROM socios")
        socios = self.cursor.fetchall()
        return socios

    def eliminar_socio(self, codigo):
        self.cursor.execute(f"DELETE FROM socios WHERE codigo = {codigo}")
        self.conn.commit()
        return self.cursor.rowcount > 0


# Programa principal (inicializo el catálogo)
catalogo = Catalogo(host='KariT.mysql.pythonanywhere-services.com', user='KariT', password='pass123456', database='KariT$miapp')

ruta_destino = '/home/KariT/mysite/static/imagenes/'


@app.route("/socios", methods=["GET"])
def listar_socios():
    socios = catalogo.listar_socios()
    return jsonify(socios)


@app.route("/socios", methods=["POST"])
def agregar_socio():
    documento = request.form['documento']
    nombre = request.form['nombre']
    telefono = request.form['telefono']
    mail = request.files['mail']
    direccion = request.form['direccion']
    foto = request.form['foto']
    nombre_foto = ""

    nombre_foto = secure_filename(foto.filename)
    nombre_base, extension = os.path.splitext(nombre_foto)
    nombre_foto = f"{nombre_base}_{int(time.time())}{extension}"

    nuevo_codigo = catalogo.agregar_socio(documento, nombre, telefono, mail, direccion, nombre_foto)
    if nuevo_codigo:
        foto.save(os.path.join(ruta_destino, nombre_foto))

        return jsonify({"mensaje": "Socio agregado correctamente.", "codigo": nuevo_codigo, "foto": nombre_foto}), 201
    else:
        return jsonify({"mensaje": "Error al agregar el socio."}), 500


@app.route("/socios/<int:codigo>", methods=["PUT"])
def modificar_socio(codigo):
    nuevo_documento = request.form.get("documento")
    nuevo_nombre = request.form.get("nombre")
    nuevo_telefono = request.form.get("telefono")
    nuevo_mail = request.form.get("mail")
    nueva_direccion = request.form.get("direccion")

    if 'foto' in request.files:
        foto = request.files['foto']
        nombre_foto = secure_filename(foto.filename)
        nombre_base, extension = os.path.splitext(nombre_foto)
        nombre_foto = f"{nombre_base}_{int(time.time())}{extension}"

        foto.save(os.path.join(ruta_destino, nombre_foto))

        socio = catalogo.consultar_socio(codigo)
        if socio:
            foto_vieja = socio["foto_url"]
            ruta_foto = os.path.join(ruta_destino, foto_vieja)

            if os.path.exists(ruta_foto):
                os.remove(ruta_foto)
    else:
        socio = catalogo.consultar_socio(codigo)
        if socio:
            nombre_foto = socio["foto_url"]

    if catalogo.modificar_socio(codigo, nuevo_documento, nuevo_nombre, nuevo_telefono, nuevo_mail, nueva_direccion, nombre_foto):
        return jsonify({"mensaje": "Socio modificado"}), 200
    else:
        return jsonify({"mensaje": "Socio no encontrado"}), 403


@app.route("/socios/<int:codigo>", methods=["DELETE"])
def eliminar_socio(codigo):

    socio = catalogo.consultar_socio(codigo)
    if socio:
        ruta_foto = os.path.join(ruta_destino, socio['foto_url'])
        if os.path.exists(ruta_foto):
            os.remove(ruta_foto)

        if catalogo.eliminar_socio(codigo):
            return jsonify({"mensaje": "Socio eliminado"}), 200
        else:
            return jsonify({"mensaje": "Error al eliminar el socio"}), 500
    else:
        return jsonify({"mensaje": "Socio no encontrado"}), 404


if __name__ == "__main__":
    app.run(debug=True)
