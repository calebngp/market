#!/usr/bin/env python3
"""
Módulo de Reconocimiento Facial
Usa la librería face_recognition para identificar usuarios
"""

import numpy as np
import json
import os
from PIL import Image
import io
import base64


# Archivo para almacenar los encodings faciales de los usuarios
FACIAL_ENCODINGS_FILE = 'facial_encodings.json'


def load_facial_encodings():
    """Carga los encodings faciales desde el archivo JSON"""
    if os.path.exists(FACIAL_ENCODINGS_FILE):
        with open(FACIAL_ENCODINGS_FILE, 'r', encoding='utf-8') as file:
            data = json.load(file)
            # Convertir las listas de vuelta a numpy arrays
            encodings = {}
            for user_id, encoding_list in data.items():
                encodings[user_id] = np.array(encoding_list)
            return encodings
    return {}


def save_facial_encodings(encodings):
    """Guarda los encodings faciales en un archivo JSON"""
    # Convertir numpy arrays a listas para JSON
    data = {}
    for user_id, encoding in encodings.items():
        data[user_id] = encoding.tolist()
    
    with open(FACIAL_ENCODINGS_FILE, 'w', encoding='utf-8') as file:
        json.dump(data, file)


def encode_face_from_image(image_data):
    """
    Codifica un rostro desde una imagen
    
    Args:
        image_data: Datos de la imagen (bytes, base64 string, o numpy array)
    
    Returns:
        encoding: Array numpy con el encoding del rostro, o None si no se encuentra rostro
    """
    try:
        # Import lazy para evitar que el servidor crashee si face_recognition/dlib falla al cargar
        try:
            import face_recognition  # type: ignore
        except Exception as e:
            print(f"Reconocimiento facial deshabilitado: no se pudo importar face_recognition ({e})")
            return None

        # Si es base64, decodificarlo
        if isinstance(image_data, str):
            if image_data.startswith('data:image'):
                # Remover el prefijo data:image/...;base64,
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
        elif isinstance(image_data, bytes):
            image = Image.open(io.BytesIO(image_data))
        else:
            image = image_data
        
        # Convertir a RGB si es necesario
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convertir PIL Image a numpy array
        image_array = np.array(image)
        
        # Detectar y codificar el rostro
        face_encodings = face_recognition.face_encodings(image_array)
        
        if len(face_encodings) == 0:
            return None
        
        # Retornar el primer rostro encontrado
        return face_encodings[0]
    
    except Exception as e:
        print(f"Error al codificar rostro: {e}")
        return None


def register_user_face(user_id, image_data):
    """
    Registra el rostro de un usuario
    
    Args:
        user_id: ID del usuario
        image_data: Datos de la imagen con el rostro
    
    Returns:
        dict: {'success': bool, 'message': str}
    """
    encoding = encode_face_from_image(image_data)
    
    if encoding is None:
        return {
            'success': False,
            'message': 'No se pudo detectar un rostro en la imagen. Asegúrate de que haya una persona visible.'
        }
    
    # Cargar encodings existentes
    encodings = load_facial_encodings()
    
    # Guardar el encoding del usuario
    encodings[user_id] = encoding
    
    # Guardar en archivo
    save_facial_encodings(encodings)
    
    return {
        'success': True,
        'message': f'Rostro registrado exitosamente para el usuario {user_id}'
    }


def recognize_face(image_data, tolerance=0.6):
    """
    Reconoce un rostro en una imagen y lo compara con los usuarios registrados
    
    Args:
        image_data: Datos de la imagen con el rostro
        tolerance: Tolerancia para la comparación (menor = más estricto, default 0.6)
    
    Returns:
        dict: {'success': bool, 'user_id': str o None, 'distance': float o None, 'message': str}
    """
    # Import lazy para evitar crash al importar el módulo completo
    try:
        import face_recognition  # type: ignore
    except Exception as e:
        return {
            'success': False,
            'user_id': None,
            'distance': None,
            'message': f'Reconocimiento facial no disponible (error al cargar dependencias): {e}'
        }

    # Codificar el rostro de la imagen
    encoding = encode_face_from_image(image_data)
    
    if encoding is None:
        return {
            'success': False,
            'user_id': None,
            'distance': None,
            'message': 'No se pudo detectar un rostro en la imagen'
        }
    
    # Cargar encodings de usuarios registrados
    known_encodings = load_facial_encodings()
    
    if not known_encodings:
        return {
            'success': False,
            'user_id': None,
            'distance': None,
            'message': 'No hay usuarios registrados con reconocimiento facial'
        }
    
    # Comparar con cada usuario registrado
    best_match = None
    best_distance = float('inf')
    
    for user_id, known_encoding in known_encodings.items():
        # Calcular la distancia entre los encodings
        distance = face_recognition.face_distance([known_encoding], encoding)[0]
        
        if distance < best_distance:
            best_distance = distance
            best_match = user_id
    
    # Verificar si la distancia está dentro de la tolerancia
    if best_distance <= tolerance:
        return {
            'success': True,
            'user_id': best_match,
            'distance': float(best_distance),
            'message': f'Usuario reconocido: {best_match}'
        }
    else:
        return {
            'success': False,
            'user_id': None,
            'distance': float(best_distance),
            'message': f'No se encontró una coincidencia. Distancia mínima: {best_distance:.2f}'
        }


def has_facial_encoding(user_id):
    """Verifica si un usuario tiene un encoding facial registrado"""
    encodings = load_facial_encodings()
    return user_id in encodings


def delete_user_face(user_id):
    """Elimina el encoding facial de un usuario"""
    encodings = load_facial_encodings()
    
    if user_id in encodings:
        del encodings[user_id]
        save_facial_encodings(encodings)
        return {
            'success': True,
            'message': f'Rostro eliminado para el usuario {user_id}'
        }
    
    return {
        'success': False,
        'message': f'No se encontró un rostro registrado para el usuario {user_id}'
    }
