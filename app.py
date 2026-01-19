#!/usr/bin/env python3
"""
Sistema de Código de Barras - Market
Servidor Flask con base de datos CSV
"""

import csv
import os
from flask import Flask, render_template, request, jsonify
from facial_recognition import (
    register_user_face,
    recognize_face,
    has_facial_encoding,
    delete_user_face
)

app = Flask(__name__)

# Ruta del archivo CSV
CSV_FILE = 'products.csv'
USERS_FILE = 'users.csv'

# Porcentaje de reintegro en compras (10%)
REINTEGRO_PORCENTAJE = 10

# Diccionarios de referencia para códigos de barras
PAISES = {
    "13": "Paraguay",
    "45": "Argentina",
    "50": "Brasil",
    "78": "México",
    "84": "España",
}

CATEGORIAS = [
    "Bebidas",
    "Alimentos",
    "Lácteos",
    "Calzado",
    "Electrónica",
    "Limpieza",
    "Higiene",
    "Otros"
]

PROVEEDORES = {
    "64": "Proveedor Guaraní S.A.",
    "12": "Distribuidora Mercosur",
    "45": "TechPlus Importaciones",
    "33": "Importadora del Este",
    "77": "Comercial Paraguay",
}


def init_users_file():
    """Inicializa el archivo de usuarios con el usuario por defecto"""
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['id', 'nombre', 'puntos'])
            writer.writeheader()
            writer.writerow({
                'id': '1',
                'nombre': 'Caleb Medina',
                'puntos': '1000'
            })


def read_users():
    """Lee todos los usuarios del CSV"""
    users = []
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                users.append(row)
    return users


def write_users(users):
    """Escribe los usuarios al CSV"""
    if users:
        fieldnames = ['id', 'nombre', 'puntos']
        with open(USERS_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(users)


def get_default_user():
    """Obtiene el usuario por defecto (Caleb Medina)"""
    users = read_users()
    if users:
        # Buscar Caleb Medina
        for user in users:
            if user['nombre'] == 'Caleb Medina':
                return user
        # Si no existe, retornar el primero
        return users[0] if users else None
    return None


def calculate_product_points(precio):
    """Calcula los puntos de un producto basado en su precio (1 punto por cada 100 guaraníes)"""
    return int(float(precio) / 100)


def calculate_reintegro(puntos_usados):
    """Calcula el reintegro de puntos para próximas compras"""
    return int(puntos_usados * (REINTEGRO_PORCENTAJE / 100))


def read_products():
    """Lee todos los productos del CSV"""
    products = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                products.append(row)
    return products


def write_products(products):
    """Escribe los productos al CSV"""
    if products:
        fieldnames = ['codigo', 'nombre', 'categoria', 'precio', 'pais', 'proveedor', 'stock']
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(products)


def find_product_by_code(code):
    """Busca un producto por su código de barras"""
    products = read_products()
    for product in products:
        if product['codigo'] == code:
            return product
    return None


def decode_barcode(code):
    """Decodifica información del código de barras según su estructura"""
    if len(code) < 7:
        return None
    
    pais_id = code[0:2]
    producto_id = code[2:5]
    proveedor_id = code[5:7]
    
    return {
        'pais_codigo': pais_id,
        'pais_nombre': PAISES.get(pais_id, "Desconocido"),
        'producto_id': producto_id,
        'proveedor_codigo': proveedor_id,
        'proveedor_nombre': PROVEEDORES.get(proveedor_id, "Desconocido")
    }


@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')


@app.route('/scanner')
def scanner():
    """Página del escáner de códigos de barras"""
    return render_template('scanner.html')


@app.route('/creator')
def creator():
    """Página para crear códigos de barras"""
    return render_template('creator.html', 
                         paises=PAISES, 
                         categorias=CATEGORIAS,
                         proveedores=PROVEEDORES)


@app.route('/inventory')
def inventory():
    """Página de inventario"""
    products = read_products()
    return render_template('inventory.html', products=products)


@app.route('/facial-recognition')
def facial_recognition():
    """Página de reconocimiento facial"""
    users = read_users()
    return render_template('facial_recognition.html', users=users)


@app.route('/dashboard')
def dashboard():
    """Dashboard de gestión de usuarios"""
    users = read_users()
    # Agregar información de reconocimiento facial a cada usuario
    total_points = 0
    users_with_facial = 0
    for user in users:
        user['has_facial'] = has_facial_encoding(user['id'])
        total_points += int(user.get('puntos', 0))
        if user['has_facial']:
            users_with_facial += 1
    
    return render_template('dashboard.html', 
                         users=users, 
                         total_users=len(users),
                         users_with_facial=users_with_facial,
                         total_points=total_points)


@app.route('/api/product/<code>')
def get_product(code):
    """API para obtener un producto por código"""
    product = find_product_by_code(code)
    if product:
        decoded = decode_barcode(code)
        # Calcular puntos del producto
        puntos = calculate_product_points(product['precio'])
        product_with_points = product.copy()
        product_with_points['puntos'] = puntos
        return jsonify({
            'success': True,
            'product': product_with_points,
            'decoded': decoded
        })
    return jsonify({
        'success': False,
        'message': 'Producto no encontrado'
    })


@app.route('/api/product', methods=['POST'])
def add_product():
    """API para agregar un nuevo producto"""
    data = request.json
    
    # Validar datos requeridos
    required = ['codigo', 'nombre', 'categoria', 'precio', 'pais', 'proveedor', 'stock']
    for field in required:
        if field not in data or not data[field]:
            return jsonify({
                'success': False,
                'message': f'Campo requerido: {field}'
            })
    
    # Verificar si el código ya existe
    if find_product_by_code(data['codigo']):
        return jsonify({
            'success': False,
            'message': 'Ya existe un producto con este código'
        })
    
    # Agregar el producto
    products = read_products()
    products.append({
        'codigo': data['codigo'],
        'nombre': data['nombre'],
        'categoria': data['categoria'],
        'precio': data['precio'],
        'pais': data['pais'],
        'proveedor': data['proveedor'],
        'stock': data['stock']
    })
    write_products(products)
    
    return jsonify({
        'success': True,
        'message': 'Producto agregado correctamente'
    })


@app.route('/api/product/<code>', methods=['PUT'])
def update_product(code):
    """API para actualizar un producto"""
    data = request.json
    products = read_products()
    
    for i, product in enumerate(products):
        if product['codigo'] == code:
            products[i].update(data)
            write_products(products)
            return jsonify({
                'success': True,
                'message': 'Producto actualizado'
            })
    
    return jsonify({
        'success': False,
        'message': 'Producto no encontrado'
    })


@app.route('/api/product/<code>', methods=['DELETE'])
def delete_product(code):
    """API para eliminar un producto"""
    products = read_products()
    new_products = [p for p in products if p['codigo'] != code]
    
    if len(new_products) == len(products):
        return jsonify({
            'success': False,
            'message': 'Producto no encontrado'
        })
    
    write_products(new_products)
    return jsonify({
        'success': True,
        'message': 'Producto eliminado'
    })


@app.route('/api/products')
def get_all_products():
    """API para obtener todos los productos"""
    products = read_products()
    return jsonify({
        'success': True,
        'products': products
    })


@app.route('/api/user/current')
def get_current_user():
    """API para obtener el usuario actual (Caleb Medina por defecto)"""
    user = get_default_user()
    if user:
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'nombre': user['nombre'],
                'puntos': int(user['puntos'])
            }
        })
    return jsonify({
        'success': False,
        'message': 'Usuario no encontrado'
    })


@app.route('/api/purchase', methods=['POST'])
def purchase_with_points():
    """API para comprar un producto usando puntos"""
    data = request.json
    
    # Validar datos
    if 'product_code' not in data:
        return jsonify({
            'success': False,
            'message': 'Código de producto requerido'
        })
    
    # Obtener producto
    product = find_product_by_code(data['product_code'])
    if not product:
        return jsonify({
            'success': False,
            'message': 'Producto no encontrado'
        })
    
    # Calcular puntos necesarios
    puntos_necesarios = calculate_product_points(product['precio'])
    
    # Obtener usuario actual
    user = get_default_user()
    if not user:
        return jsonify({
            'success': False,
            'message': 'Usuario no encontrado'
        })
    
    puntos_actuales = int(user['puntos'])
    
    # Verificar si tiene suficientes puntos
    if puntos_actuales < puntos_necesarios:
        return jsonify({
            'success': False,
            'message': f'Puntos insuficientes. Necesitas {puntos_necesarios} puntos, tienes {puntos_actuales}'
        })
    
    # Calcular reintegro
    reintegro = calculate_reintegro(puntos_necesarios)
    
    # Actualizar puntos del usuario
    users = read_users()
    nuevos_puntos = puntos_actuales - puntos_necesarios + reintegro
    
    for i, u in enumerate(users):
        if u['id'] == user['id']:
            users[i]['puntos'] = str(nuevos_puntos)
            break
    
    write_users(users)
    
    return jsonify({
        'success': True,
        'message': 'Compra realizada exitosamente',
        'purchase': {
            'product': product['nombre'],
            'puntos_usados': puntos_necesarios,
            'reintegro': reintegro,
            'puntos_anteriores': puntos_actuales,
            'puntos_nuevos': nuevos_puntos
        }
    })


@app.route('/api/facial/register', methods=['POST'])
def register_facial():
    """API para registrar el rostro de un usuario"""
    data = request.json
    
    if 'user_id' not in data or 'image' not in data:
        return jsonify({
            'success': False,
            'message': 'Se requiere user_id e image'
        })
    
    user_id = data['user_id']
    image_data = data['image']
    
    # Verificar que el usuario existe
    users = read_users()
    user_exists = any(u['id'] == user_id for u in users)
    
    if not user_exists:
        return jsonify({
            'success': False,
            'message': 'Usuario no encontrado'
        })
    
    # Registrar el rostro
    result = register_user_face(user_id, image_data)
    return jsonify(result)


@app.route('/api/facial/recognize', methods=['POST'])
def recognize_facial():
    """API para reconocer un usuario desde una imagen"""
    data = request.json
    
    if 'image' not in data:
        return jsonify({
            'success': False,
            'message': 'Se requiere image'
        })
    
    image_data = data['image']
    tolerance = data.get('tolerance', 0.6)
    
    # Reconocer el rostro
    result = recognize_face(image_data, tolerance)
    
    if result['success']:
        # Obtener información del usuario reconocido
        user_id = result['user_id']
        users = read_users()
        user = next((u for u in users if u['id'] == user_id), None)
        
        if user:
            result['user'] = {
                'id': user['id'],
                'nombre': user['nombre'],
                'puntos': int(user['puntos'])
            }
    
    return jsonify(result)


@app.route('/api/facial/check/<user_id>')
def check_facial_encoding(user_id):
    """API para verificar si un usuario tiene reconocimiento facial registrado"""
    has_encoding = has_facial_encoding(user_id)
    return jsonify({
        'success': True,
        'has_encoding': has_encoding
    })


@app.route('/api/facial/delete/<user_id>', methods=['DELETE'])
def delete_facial(user_id):
    """API para eliminar el reconocimiento facial de un usuario"""
    result = delete_user_face(user_id)
    return jsonify(result)


@app.route('/api/user', methods=['POST'])
def create_user():
    """API para crear un nuevo usuario"""
    data = request.json
    
    if 'nombre' not in data or not data['nombre']:
        return jsonify({
            'success': False,
            'message': 'El nombre es requerido'
        })
    
    users = read_users()
    
    # Generar nuevo ID
    if users:
        max_id = max(int(u['id']) for u in users)
        new_id = str(max_id + 1)
    else:
        new_id = '1'
    
    # Verificar si el nombre ya existe
    if any(u['nombre'].lower() == data['nombre'].lower() for u in users):
        return jsonify({
            'success': False,
            'message': 'Ya existe un usuario con ese nombre'
        })
    
    # Crear nuevo usuario
    new_user = {
        'id': new_id,
        'nombre': data['nombre'],
        'puntos': str(data.get('puntos', 0))
    }
    
    users.append(new_user)
    write_users(users)
    
    return jsonify({
        'success': True,
        'message': 'Usuario creado exitosamente',
        'user': new_user
    })


@app.route('/api/user/<user_id>', methods=['PUT'])
def update_user(user_id):
    """API para actualizar un usuario"""
    data = request.json
    users = read_users()
    
    user_found = False
    for i, user in enumerate(users):
        if user['id'] == user_id:
            # Actualizar campos permitidos
            if 'nombre' in data:
                # Verificar que el nombre no esté duplicado
                if any(u['nombre'].lower() == data['nombre'].lower() and u['id'] != user_id for u in users):
                    return jsonify({
                        'success': False,
                        'message': 'Ya existe otro usuario con ese nombre'
                    })
                users[i]['nombre'] = data['nombre']
            
            if 'puntos' in data:
                users[i]['puntos'] = str(data['puntos'])
            
            user_found = True
            break
    
    if not user_found:
        return jsonify({
            'success': False,
            'message': 'Usuario no encontrado'
        })
    
    write_users(users)
    
    return jsonify({
        'success': True,
        'message': 'Usuario actualizado exitosamente',
        'user': users[i] if user_found else None
    })


@app.route('/api/user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """API para eliminar un usuario"""
    users = read_users()
    new_users = [u for u in users if u['id'] != user_id]
    
    if len(new_users) == len(users):
        return jsonify({
            'success': False,
            'message': 'Usuario no encontrado'
        })
    
    # Eliminar también el reconocimiento facial si existe
    if has_facial_encoding(user_id):
        delete_user_face(user_id)
    
    write_users(new_users)
    
    return jsonify({
        'success': True,
        'message': 'Usuario eliminado exitosamente'
    })


@app.route('/api/users')
def get_all_users():
    """API para obtener todos los usuarios con información de reconocimiento facial"""
    users = read_users()
    
    # Agregar información de reconocimiento facial
    for user in users:
        user['has_facial'] = has_facial_encoding(user['id'])
    
    return jsonify({
        'success': True,
        'users': users
    })


if __name__ == '__main__':
    import ssl
    import os
    
    # Inicializar archivo de usuarios
    init_users_file()
    
    print("\n🚀 Servidor iniciado!")
    print("=" * 50)
    
    # Verificar si existen certificados SSL
    cert_exists = os.path.exists('cert.pem') and os.path.exists('key.pem')
    
    if cert_exists:
        print("🔒 HTTPS habilitado (certificado autofirmado)")
        print("📍 Acceso local: https://localhost:3000")
        print("📍 Acceso red local: https://<tu-ip>:3000")
        print("\n⚠️  Tu navegador mostrará advertencia de seguridad.")
        print("   Haz clic en 'Avanzado' → 'Continuar' para aceptar.")
    else:
        print("📍 Acceso local: http://localhost:3000")
        print("📍 Acceso red local: http://<tu-ip>:3000")
        print("\n⚠️  Sin HTTPS: la cámara solo funciona en localhost")
    
    print("=" * 50)
    print("Presiona Ctrl+C para detener el servidor\n")
    
    if cert_exists:
        # Ejecutar con HTTPS
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain('cert.pem', 'key.pem')
        app.run(host='0.0.0.0', port=3000, debug=True, ssl_context=context)
    else:
        # Ejecutar sin HTTPS
        app.run(host='0.0.0.0', port=3000, debug=True)
