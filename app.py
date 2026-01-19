#!/usr/bin/env python3
"""
Sistema de Código de Barras - Market
Servidor Flask con base de datos CSV
"""

import csv
import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Ruta del archivo CSV
CSV_FILE = 'products.csv'

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


@app.route('/api/product/<code>')
def get_product(code):
    """API para obtener un producto por código"""
    product = find_product_by_code(code)
    if product:
        decoded = decode_barcode(code)
        return jsonify({
            'success': True,
            'product': product,
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


if __name__ == '__main__':
    import ssl
    import os
    
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
