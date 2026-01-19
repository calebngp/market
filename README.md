# 📦 Market - Sistema de Código de Barras

Sistema web para gestionar productos mediante códigos de barras, con escáner de cámara y generador de códigos personalizados.

## 🚀 Características

- **Escáner de códigos de barras** - Usa la cámara del dispositivo para escanear códigos
- **Generador de códigos** - Crea códigos de barras personalizados con diferentes formatos
- **Base de datos CSV** - Almacenamiento simple de productos
- **Interfaz moderna** - Diseño oscuro con animaciones fluidas
- **Red local** - Accesible desde cualquier dispositivo en la misma red

## 📋 Requisitos

- Python 3.8+
- Flask

## ⚡ Instalación

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
python app.py
```

## 🌐 Acceso

- **Local**: http://localhost:3000
- **Red Local**: http://[TU-IP]:3000

Para encontrar tu IP:
- Windows: `ipconfig`
- Mac/Linux: `ifconfig` o `ip addr`

## 📱 Páginas

| Ruta | Descripción |
|------|-------------|
| `/` | Página principal con menú |
| `/scanner` | Escáner de códigos con cámara |
| `/creator` | Crear nuevos códigos de barras |
| `/inventory` | Ver y gestionar inventario |

## 🏷️ Estructura del Código de Barras

```
[PP][PPP][SS]
│   │    └── Proveedor (2 dígitos)
│   └─────── Producto (3 dígitos)
└─────────── País (2 dígitos)
```

### Códigos de País
- `13` - Paraguay
- `45` - Argentina
- `50` - Brasil
- `78` - México
- `84` - España

### Códigos de Proveedor
- `64` - Proveedor Guaraní S.A.
- `12` - Distribuidora Mercosur
- `45` - TechPlus Importaciones
- `33` - Importadora del Este
- `77` - Comercial Paraguay

## 📡 API REST

### GET `/api/product/<codigo>`
Obtiene información de un producto.

### POST `/api/product`
Crea un nuevo producto.
```json
{
  "codigo": "1345364",
  "nombre": "Producto",
  "categoria": "Categoría",
  "precio": 25000,
  "pais": "Paraguay",
  "proveedor": "Proveedor",
  "stock": 100
}
```

### PUT `/api/product/<codigo>`
Actualiza un producto existente.

### DELETE `/api/product/<codigo>`
Elimina un producto.

### GET `/api/products`
Lista todos los productos.

## 📁 Estructura de Archivos

```
market/
├── app.py              # Servidor Flask
├── products.csv        # Base de datos
├── requirements.txt    # Dependencias
├── README.md
└── templates/
    ├── index.html      # Página principal
    ├── scanner.html    # Escáner
    ├── creator.html    # Creador de códigos
    └── inventory.html  # Inventario
```
# market
