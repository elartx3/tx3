from flask import Flask, request, jsonify
import os
import time
from groq import Groq

app = Flask(__name__)

def get_response(api_key, user_content, model_choice, system_content="You are a helpful assistant.",
                 temperature=1.0, max_tokens=1024, top_p=1.0):
    # Crear cliente Groq con la API Key proporcionada
    client = Groq(api_key=api_key)
    
    # Construir los mensajes para la API
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content}
    ]

    # Intentar hacer la solicitud con manejo de límites de tasa
    def make_request():
        response = client.chat.completions.create(
            messages=messages,
            model=model_choice,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p
        )
        return response

    try:
        response = make_request()
    except Exception as e:
        if hasattr(e, 'status_code') and e.status_code == 429:
            # Si la solicitud se bloquea por límite de tasa, espera el tiempo indicado en el header "retry-after"
            retry_after = int(e.headers.get('retry-after', 1))
            time.sleep(retry_after + 2)  # Añadir un pequeño buffer para mayor seguridad
            response = make_request()
        else:
            return {"error": str(e)}

    # Devolver la respuesta generada
    return response.choices[0].message.content

# Ruta de la raíz que devuelve un "Hello, World!"
@app.route('/')
def home():
    return "Hello, World!"

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json

    # Verificar que se proporciona la API Key
    api_key = data.get('api_key')
    if not api_key:
        return jsonify({"error": "API Key is required"}), 400

    # Obtener los parámetros de la solicitud o usar valores por defecto
    user_content = data.get('user_content')
    model_choice = data.get('model_choice', 'mixtral-8x7b-32768')  # Valor por defecto
    system_content = data.get('system_content', "You are a helpful assistant.")
    temperature = data.get('temperature', 1.0)
    max_tokens = data.get('max_tokens', 1024)
    top_p = data.get('top_p', 1.0)

    if not user_content:
        return jsonify({"error": "No user_content provided"}), 400

    response = get_response(api_key, user_content, model_choice, system_content, temperature, max_tokens, top_p)
    
    if isinstance(response, dict) and "error" in response:
        return jsonify(response), 500

    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
