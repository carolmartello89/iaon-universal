#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IAON Universal - Vercel Deploy
Assistente IA que funciona em qualquer dispositivo
Otimizado para deploy no Vercel
"""

from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import json
from datetime import datetime
import uuid

# Configuração da aplicação
app = Flask(__name__)
CORS(app, origins="*")

# Configuração do banco de dados
DATABASE = 'iaon.db'

def init_db():
    """Inicializa o banco de dados"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Tabela de organizações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            organization_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (organization_id) REFERENCES organizations (id)
        )
    ''')
    
    # Tabela de conversas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT NOT NULL,
            response TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Inserir organização padrão se não existir
    cursor.execute('SELECT COUNT(*) FROM organizations')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO organizations (name) VALUES (?)', ('IAON Universal',))
    
    conn.commit()
    conn.close()

# Template HTML principal
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 IAON - Assistente IA Universal</title>
    
    <!-- PWA Meta Tags -->
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#667eea">
    <link rel="apple-touch-icon" href="/icon-192.png">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            height: 100vh;
            overflow: hidden;
        }
        
        .container {
            display: flex;
            flex-direction: column;
            height: 100vh;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            padding: 20px 0;
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            margin-bottom: 20px;
        }
        
        .chat-container {
            flex: 1;
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 20px;
            margin-bottom: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
        }
        
        .messages {
            flex: 1;
            overflow-y: auto;
            margin-bottom: 20px;
        }
        
        .message {
            margin: 15px 0;
            padding: 15px;
            border-radius: 15px;
            max-width: 80%;
            word-wrap: break-word;
        }
        
        .user-message {
            background: rgba(76,175,80,0.3);
            margin-left: auto;
            border: 1px solid #4CAF50;
        }
        
        .bot-message {
            background: rgba(33,150,243,0.3);
            margin-right: auto;
            border: 1px solid #2196F3;
        }
        
        .input-container {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 20px;
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .chat-input {
            flex: 1;
            padding: 15px;
            border: none;
            border-radius: 15px;
            background: rgba(255,255,255,0.2);
            color: white;
            font-size: 16px;
        }
        
        .chat-input::placeholder {
            color: rgba(255,255,255,0.7);
        }
        
        .btn {
            padding: 15px 20px;
            border: none;
            border-radius: 15px;
            background: #4CAF50;
            color: white;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.3s;
        }
        
        .btn:hover {
            background: #45a049;
            transform: translateY(-2px);
        }
        
        .btn:disabled {
            background: rgba(255,255,255,0.3);
            cursor: not-allowed;
        }
        
        .voice-btn {
            background: #FF5722;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .voice-btn.recording {
            background: #F44336;
            animation: pulse 1s infinite;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
        
        .device-info {
            background: rgba(255,255,255,0.1);
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 10px;
            font-size: 0.9em;
            text-align: center;
        }
        
        .status {
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(76,175,80,0.9);
            padding: 10px 15px;
            border-radius: 10px;
            font-size: 0.9em;
            z-index: 1000;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .message {
                max-width: 90%;
            }
            
            .input-container {
                flex-direction: column;
                gap: 15px;
            }
            
            .chat-input {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div id="status" class="status" style="display: none;">🌍 IAON Vercel - Online</div>
    
    <div class="container">
        <div class="header">
            <h1>🤖 IAON</h1>
            <p>Assistente IA Universal - Vercel Deploy</p>
            <div id="deviceInfo" class="device-info"></div>
        </div>
        
        <div class="chat-container">
            <div id="messages" class="messages">
                <div class="message bot-message">
                    👋 Olá! Sou o IAON, seu assistente IA universal!<br>
                    🌍 Agora funcionando globalmente via Vercel!<br>
                    💬 Digite uma pergunta ou 🎤 use o microfone.
                </div>
            </div>
        </div>
        
        <div class="input-container">
            <input type="text" id="chatInput" class="chat-input" placeholder="Digite sua pergunta..." maxlength="500">
            <button id="sendBtn" class="btn">📤 Enviar</button>
            <button id="voiceBtn" class="btn voice-btn">🎤</button>
        </div>
    </div>

    <script>
        // Variáveis globais
        let isRecording = false;
        let recognition = null;
        
        // Elementos DOM
        const messagesDiv = document.getElementById('messages');
        const chatInput = document.getElementById('chatInput');
        const sendBtn = document.getElementById('sendBtn');
        const voiceBtn = document.getElementById('voiceBtn');
        const deviceInfo = document.getElementById('deviceInfo');
        const status = document.getElementById('status');
        
        // Detectar dispositivo
        function detectDevice() {
            const userAgent = navigator.userAgent;
            let device = 'Desktop';
            let browser = 'Unknown';
            
            if (/iPad|iPhone|iPod/.test(userAgent)) {
                device = 'iPhone/iPad';
                browser = 'Safari';
            } else if (/Android/.test(userAgent)) {
                device = 'Android';
                browser = /Chrome/.test(userAgent) ? 'Chrome' : 'Other';
            } else if (/Windows/.test(userAgent)) {
                device = 'Windows';
                browser = /Chrome/.test(userAgent) ? 'Chrome' : /Firefox/.test(userAgent) ? 'Firefox' : 'Other';
            }
            
            deviceInfo.innerHTML = `📱 ${device} • 🌐 ${browser} • 🌍 Vercel Deploy`;
            return { device, browser };
        }
        
        // Inicializar reconhecimento de voz
        function initVoiceRecognition() {
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                recognition = new SpeechRecognition();
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.lang = 'pt-BR';
                
                recognition.onstart = function() {
                    isRecording = true;
                    voiceBtn.classList.add('recording');
                    voiceBtn.innerHTML = '🔴';
                };
                
                recognition.onresult = function(event) {
                    const transcript = event.results[0][0].transcript;
                    chatInput.value = transcript;
                    sendMessage();
                };
                
                recognition.onend = function() {
                    isRecording = false;
                    voiceBtn.classList.remove('recording');
                    voiceBtn.innerHTML = '🎤';
                };
                
                recognition.onerror = function(event) {
                    console.error('Erro no reconhecimento de voz:', event.error);
                    isRecording = false;
                    voiceBtn.classList.remove('recording');
                    voiceBtn.innerHTML = '🎤';
                    addMessage('❌ Erro no reconhecimento de voz. Use o chat por texto.', 'bot');
                };
                
                return true;
            }
            return false;
        }
        
        // Adicionar mensagem ao chat
        function addMessage(text, sender) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            messageDiv.innerHTML = text.replace(/\\n/g, '<br>');
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        // Enviar mensagem
        async function sendMessage() {
            const message = chatInput.value.trim();
            if (!message) return;
            
            addMessage(message, 'user');
            chatInput.value = '';
            sendBtn.disabled = true;
            sendBtn.innerHTML = '⏳ Processando...';
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });
                
                const data = await response.json();
                addMessage(data.response || '❌ Erro ao processar resposta', 'bot');
            } catch (error) {
                console.error('Erro:', error);
                addMessage('❌ Erro de conexão. Tente novamente.', 'bot');
            } finally {
                sendBtn.disabled = false;
                sendBtn.innerHTML = '📤 Enviar';
            }
        }
        
        // Event listeners
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        sendBtn.addEventListener('click', sendMessage);
        
        voiceBtn.addEventListener('click', function() {
            if (!recognition) {
                addMessage('❌ Reconhecimento de voz não suportado neste navegador/dispositivo.', 'bot');
                return;
            }
            
            if (isRecording) {
                recognition.stop();
            } else {
                recognition.start();
            }
        });
        
        // Inicialização
        window.addEventListener('load', function() {
            detectDevice();
            const voiceSupported = initVoiceRecognition();
            
            if (!voiceSupported) {
                voiceBtn.style.display = 'none';
                addMessage('💬 Reconhecimento de voz não disponível. Use o chat por texto.', 'bot');
            }
            
            status.style.display = 'block';
            setTimeout(() => {
                status.style.display = 'none';
            }, 3000);
            
            chatInput.focus();
        });
        
        // Service Worker para PWA
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js').catch(console.error);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Página principal"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/chat', methods=['POST'])
def chat_api():
    """API de chat"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Mensagem vazia'}), 400
        
        # Processar mensagem
        response = process_message(user_message)
        
        # Salvar no banco de dados
        save_conversation(user_message, response)
        
        return jsonify({'response': response})
    
    except Exception as e:
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

def process_message(message):
    """Processar mensagem do usuário"""
    message_lower = message.lower()
    
    # Respostas baseadas em palavras-chave
    if any(word in message_lower for word in ['oi', 'olá', 'hello', 'bom dia', 'boa tarde', 'boa noite']):
        return "👋 Olá! Como posso ajudá-lo hoje? Sou o IAON, seu assistente IA universal, agora funcionando globalmente via Vercel!"
    
    elif any(word in message_lower for word in ['como você está', 'tudo bem', 'como vai']):
        return "😊 Estou muito bem, obrigado! Funcionando perfeitamente no Vercel com HTTPS seguro. Como posso ajudá-lo?"
    
    elif any(word in message_lower for word in ['que horas', 'hora atual', 'horário']):
        now = datetime.now()
        return f"🕐 Agora são {now.strftime('%H:%M')} do dia {now.strftime('%d/%m/%Y')}."
    
    elif any(word in message_lower for word in ['nome', 'quem é você', 'o que é']):
        return "🤖 Sou o IAON (Inteligência Artificial Otimizada Neural), seu assistente IA universal! Agora funcionando globalmente via Vercel com HTTPS seguro."
    
    elif any(word in message_lower for word in ['ajuda', 'help', 'comandos']):
        return """🆘 **Como posso ajudar:**
        
💬 **Chat**: Digite qualquer pergunta
🎤 **Voz**: Use o microfone (se suportado)
🌍 **Global**: Funcionando via Vercel worldwide
📱 **PWA**: Instale como app nativo
🔒 **Seguro**: HTTPS automático

**Exemplos:**
• "Que horas são?"
• "Como você está?"
• "Me conte uma piada"
• "Qual o clima hoje?"
        """
    
    elif any(word in message_lower for word in ['piada', 'engraçado', 'humor']):
        piadas = [
            "🤖 Por que o robô foi ao médico? Porque estava com vírus! 😄",
            "💻 O que o computador foi fazer na praia? Navegar na internet! 🏖️",
            "🔋 Por que a IA não consegue mentir? Porque sempre fala a verdade binária! 😅"
        ]
        import random
        return random.choice(piadas)
    
    elif any(word in message_lower for word in ['vercel', 'deploy', 'hospedagem']):
        return """🌍 **IAON no Vercel:**
        
✅ **Deploy global** com CDN automático
✅ **HTTPS seguro** - funciona em qualquer dispositivo
✅ **Escalabilidade** automática
✅ **URL pública** mundial
✅ **PWA** instalável
✅ **Performance** otimizada

Agora você pode acessar de qualquer lugar do mundo com segurança total!
        """
    
    elif any(word in message_lower for word in ['clima', 'tempo', 'temperatura']):
        return "🌤️ Desculpe, ainda não tenho acesso a dados meteorológicos em tempo real. Mas posso ajudá-lo com outras informações!"
    
    elif any(word in message_lower for word in ['obrigado', 'valeu', 'thanks']):
        return "😊 De nada! Fico feliz em ajudar! Se precisar de mais alguma coisa, estarei aqui 24/7 via Vercel!"
    
    elif any(word in message_lower for word in ['tchau', 'bye', 'até logo']):
        return "👋 Até logo! Foi um prazer ajudá-lo. Volte sempre - estarei aqui 24/7 no Vercel!"
    
    else:
        return f"""🤔 Interessante pergunta sobre "{message}"! 

Como assistente IA, posso ajudá-lo com:
• 💬 Conversas e informações gerais
• 🕐 Horário e data atual  
• 🤖 Explicações sobre IA e tecnologia
• 😄 Piadas e entretenimento
• 🆘 Ajuda e comandos disponíveis

🌍 Funcionando globalmente via Vercel com HTTPS seguro!

Digite "ajuda" para ver todos os comandos disponíveis."""

def save_conversation(message, response):
    """Salvar conversa no banco de dados"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Inserir conversa (sem usuário específico por enquanto)
        cursor.execute('''
            INSERT INTO conversations (user_id, message, response, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (None, message, response, datetime.now()))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erro ao salvar conversa: {e}")

@app.route('/manifest.json')
def manifest():
    """Manifest PWA"""
    return jsonify({
        "name": "IAON - Assistente IA Universal",
        "short_name": "IAON",
        "description": "Assistente IA Universal - Vercel Deploy",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#667eea",
        "theme_color": "#667eea",
        "icons": [
            {
                "src": "/icon-192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/icon-512.png", 
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    })

@app.route('/sw.js')
def service_worker():
    """Service Worker"""
    return """
const CACHE_NAME = 'iaon-v1';
const urlsToCache = [
    '/',
    '/manifest.json'
];

self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                return cache.addAll(urlsToCache);
            })
    );
});

self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                if (response) {
                    return response;
                }
                return fetch(event.request);
            }
        )
    );
});
""", 200, {'Content-Type': 'application/javascript'}

@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'IAON Universal',
        'platform': 'Vercel',
        'timestamp': datetime.now().isoformat()
    })

# Inicializar banco de dados
init_db()

# Configuração para Vercel
if __name__ == '__main__':
    app.run(debug=False)
else:
    # Para Vercel
    application = app
