# Логика добавления друга по его ID-XXXX
@app.route('/add_friend', methods=['POST'])
def add_friend():
    if 'user_id' not in session:
        return redirect(url_for('auth'))

    friend_id_str = request.form.get('friend_id').strip()
    current_user = User.query.get(session['user_id'])

    if friend_id_str == current_user.user_id_str:
        flash('Нельзя добавить самого себя!')
        return redirect(url_for('index'))

    friend = User.query.filter_by(user_id_str=friend_id_str).first()
    if not friend:
        flash('Пользователь с таким ID не найден!')
        return redirect(url_for('index'))

    # Проверяем, нет ли уже такого друга
    already_friends = Friendship.query.filter_by(user_id=current_user.id, friend_id=friend.id).first()
    if already_friends:
        flash('Этот пользователь уже есть в вашем списке друзей!')
        return redirect(url_for('index'))

    # Создаем взаимную дружбу (чтобы диалог появился у обоих)
    f1 = Friendship(user_id=current_user.id, friend_id=friend.id)
    f2 = Friendship(user_id=friend.id, friend_id=current_user.id)
    db.session.add(f1)
    db.session.add(f2)
    db.session.commit()

    flash(f'Вы успешно добавили друга {friend.username}!')
    return redirect(url_for('index'))

# Выход из аккаунта
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('auth'))

# ==================== РАБОТА С ВЕБ-СОКЕТАМИ (ЧАТ) ====================

@socketio.on('join')
def on_join(data):
    # Создаем уникальное имя комнаты для пары пользователей, чтобы сообщения не путались
    user_id = data['user_id']
    friend_id = data['friend_id']
    room = f"room_{min(int(user_id), int(friend_id))}_{max(int(user_id), int(friend_id))}"
    
    join_room(room)
    
    # Загружаем историю сообщений для этой комнаты
    history = Message.query.filter_by(room_id=room).all()
    history_data = [{'text': msg.text, 'sender_id': msg.sender_id} for msg in history]
    
    emit('history', history_data)

@socketio.on('send_message')
def on_send_message(data):
    user_id = data['user_id']
    friend_id = data['friend_id']
    text = data['text'].strip()
    room = f"room_{min(int(user_id), int(friend_id))}_{max(int(user_id), int(friend_id))}"
    
    if text:
        # Сохраняем сообщение в базу данных
        new_msg = Message(sender_id=user_id, recipient_id=friend_id, text=text, room_id=room)
        db.session.add(new_msg)
        db.session.commit()
        
        # Пересылаем сообщение всем участникам комнаты
        emit('receive_message', {'text': text, 'sender_id': user_id}, room=room)

if name == '__main__':
    socketio.run(app, debug=True)
