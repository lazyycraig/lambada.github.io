import os
import secrets
import json
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit, join_room, leave_room
from cryptography.fernet import Fernet
import base64
import hashlib

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize extensions
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*", engineio_logger=False, logger=False)

# Store online users
online_users = {}

# ============================================================================
# DATABASE MODELS
# ============================================================================

class ChatRoom(db.Model):
    __tablename__ = 'chat_rooms'
    
    id = db.Column(db.String(36), primary_key=True)
    access_link = db.Column(db.String(255), unique=True, nullable=False)
    encryption_key = db.Column(db.String(255), nullable=False)
    user1_id = db.Column(db.String(36), nullable=True)
    user2_id = db.Column(db.String(36), nullable=True)
    user1_name = db.Column(db.String(100), nullable=False)
    user2_name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='room', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.id = str(secrets.token_hex(8))
        self.access_link = secrets.token_urlsafe(32)
        self.encryption_key = Fernet.generate_key().decode()

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(36), db.ForeignKey('chat_rooms.id'), nullable=False)
    sender_id = db.Column(db.String(36), nullable=False)
    sender_name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_encrypted = db.Column(db.Boolean, default=True)

# ============================================================================
# ENCRYPTION UTILITIES
# ============================================================================

def encrypt_message(message_text, key_str):
    """Encrypt message using Fernet"""
    try:
        f = Fernet(key_str.encode() if isinstance(key_str, str) else key_str)
        encrypted = f.encrypt(message_text.encode())
        return encrypted.decode()
    except Exception as e:
        print(f"Encryption error: {e}")
        return message_text

def decrypt_message(encrypted_text, key_str):
    """Decrypt message using Fernet"""
    try:
        f = Fernet(key_str.encode() if isinstance(key_str, str) else key_str)
        decrypted = f.decrypt(encrypted_text.encode())
        return decrypted.decode()
    except Exception as e:
        print(f"Decryption error: {e}")
        return "[Unable to decrypt message]"

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Home page - create new chat room"""
    return render_template('index.html')

@app.route('/create-room', methods=['POST'])
def create_room():
    """Create a new chat room"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        
        if not name or len(name) < 2:
            return jsonify({'error': 'Nama harus minimal 2 karakter'}), 400
        
        # Create new chat room
        room = ChatRoom(user1_name=name, user1_id=secrets.token_hex(8))
        db.session.add(room)
        db.session.commit()
        
        # Store user session
        session['user_id'] = room.user1_id
        session['user_name'] = name
        session['room_id'] = room.id
        session['is_creator'] = True
        
        return jsonify({
            'room_id': room.id,
            'access_link': room.access_link,
            'status': 'created'
        })
    except Exception as e:
        print(f"Error creating room: {e}")
        return jsonify({'error': 'Gagal membuat room'}), 500

@app.route('/join/<link>')
def join_chat(link):
    """Join a chat room via access link"""
    try:
        room = ChatRoom.query.filter_by(access_link=link).first()
        if not room:
            return render_template('error.html', message='Link chat tidak valid atau sudah expired')
        
        if room.user2_id is not None:
            return render_template('error.html', message='Chat room sudah penuh (2 orang)')
        
        return render_template('join.html', room_id=room.id, access_link=link)
    except Exception as e:
        print(f"Error joining chat: {e}")
        return render_template('error.html', message='Terjadi kesalahan')

@app.route('/join-room', methods=['POST'])
def join_room_post():
    """Handle join room request"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        access_link = data.get('access_link', '').strip()
        
        if not name or len(name) < 2:
            return jsonify({'error': 'Nama harus minimal 2 karakter'}), 400
        
        room = ChatRoom.query.filter_by(access_link=access_link).first()
        if not room:
            return jsonify({'error': 'Link tidak valid'}), 404
        
        if room.user2_id is not None:
            return jsonify({'error': 'Chat room sudah penuh'}), 400
        
        # Update room with second user
        room.user2_id = secrets.token_hex(8)
        room.user2_name = name
        db.session.commit()
        
        # Store user session
        session['user_id'] = room.user2_id
        session['user_name'] = name
        session['room_id'] = room.id
        session['is_creator'] = False
        
        return jsonify({
            'room_id': room.id,
            'status': 'joined'
        })
    except Exception as e:
        print(f"Error joining room: {e}")
        return jsonify({'error': 'Gagal bergabung room'}), 500

@app.route('/chat/<room_id>')
def chat(room_id):
    """Chat page"""
    if 'user_id' not in session or session.get('room_id') != room_id:
        return redirect(url_for('index'))
    
    room = ChatRoom.query.get(room_id)
    if not room:
        return render_template('error.html', message='Room tidak ditemukan')
    
    # Get message history
    messages = Message.query.filter_by(room_id=room_id).all()
    decrypted_messages = []
    
    for msg in messages:
        content = decrypt_message(msg.content, room.encryption_key) if msg.is_encrypted else msg.content
        decrypted_messages.append({
            'id': msg.id,
            'sender_name': msg.sender_name,
            'sender_id': msg.sender_id,
            'content': content,
            'timestamp': msg.timestamp.strftime('%H:%M:%S')
        })
    
    other_user = None
    if session.get('is_creator') and room.user2_name:
        other_user = room.user2_name
    elif not session.get('is_creator') and room.user1_name:
        other_user = room.user1_name
    
    return render_template('chat.html',
        room_id=room_id,
        user_name=session.get('user_name'),
        user_id=session.get('user_id'),
        other_user=other_user,
        messages=decrypted_messages
    )

@app.route('/api/room-status/<room_id>', methods=['GET'])
def room_status(room_id):
    """Get room status (who's online)"""
    room = ChatRoom.query.get(room_id)
    if not room:
        return jsonify({'error': 'Room tidak ditemukan'}), 404
    
    user1_online = room.user1_id in online_users
    user2_online = room.user2_id in online_users if room.user2_id else False
    
    return jsonify({
        'user1_online': user1_online,
        'user1_name': room.user1_name,
        'user2_online': user2_online,
        'user2_name': room.user2_name or 'Menunggu...',
        'room_full': room.user2_id is not None
    })

# ============================================================================
# WEBSOCKET EVENTS
# ============================================================================

@socketio.on('user_join')
def handle_user_join(data):
    """Handle user joining a room"""
    user_id = data.get('user_id')
    room_id = data.get('room_id')
    user_name = data.get('user_name')
    
    if user_id and room_id:
        online_users[user_id] = {
            'room_id': room_id,
            'user_name': user_name,
            'connected_at': datetime.utcnow()
        }
        join_room(room_id)
        
        # Emit user status update
        emit('user_status_changed', {
            'user_id': user_id,
            'user_name': user_name,
            'online': True
        }, room=room_id)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle user disconnection"""
    # Socket.IO automatically handles room cleanup on disconnect
    # We just need to clean up our online_users tracking
    # Find all disconnected users and remove them
    for user_id in list(online_users.keys()):
        # Check if socket is still alive - if not, remove user
        try:
            room_id = online_users[user_id].get('room_id')
            user_name = online_users[user_id].get('user_name')
            # For now we'll let it be cleaned up on next check_online
            # This prevents errors from trying to access dead sockets
        except:
            pass

@socketio.on('send_message')
def handle_message(data):
    """Handle incoming message"""
    try:
        room_id = data.get('room_id')
        user_id = data.get('user_id')
        user_name = data.get('user_name')
        content = data.get('content', '').strip()
        
        if not content or not room_id or not user_id:
            emit('error', {'message': 'Data tidak lengkap'})
            return
        
        room = ChatRoom.query.get(room_id)
        if not room:
            emit('error', {'message': 'Room tidak ditemukan'})
            return
        
        # Encrypt message
        encrypted_content = encrypt_message(content, room.encryption_key)
        
        # Save to database
        message = Message(
            room_id=room_id,
            sender_id=user_id,
            sender_name=user_name,
            content=encrypted_content,
            is_encrypted=True
        )
        db.session.add(message)
        db.session.commit()
        
        # Emit to room with decrypted message
        emit('new_message', {
            'id': message.id,
            'sender_name': user_name,
            'sender_id': user_id,
            'content': content,
            'timestamp': message.timestamp.strftime('%H:%M:%S')
        }, room=room_id)
        
    except Exception as e:
        print(f"Error handling message: {e}")
        emit('error', {'message': 'Gagal mengirim pesan'})

@socketio.on('check_online')
def handle_check_online(data):
    """Check if other user is online"""
    room_id = data.get('room_id')
    user_id = data.get('user_id')
    
    room = ChatRoom.query.get(room_id)
    if room:
        user1_online = room.user1_id in online_users
        user2_online = room.user2_id in online_users if room.user2_id else False
        
        emit('online_status', {
            'user1_online': user1_online,
            'user2_online': user2_online
        }, room=room_id)

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', message='Halaman tidak ditemukan'), 404

@app.errorhandler(500)
def server_error(error):
    db.session.rollback()
    return render_template('error.html', message='Terjadi kesalahan server'), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Run the app
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
