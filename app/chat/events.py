from flask import request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from app import socketio, db
from app.models import Message, Room, UserMetrics, RoomMembership, Rating
from app.sentiment import sentiment_analyzer
from app.moderation import check_message
from datetime import datetime
import json

@socketio.on('join')
def on_join(data):
    """Handle user joining a chat room."""
    room = Room.query.get(data['room_id'])
    if room:
        join_room(str(room.id))
        # Update user metrics and membership
        metrics = UserMetrics.query.filter_by(user_id=current_user.id).first()
        if metrics:
            metrics.rooms_joined += 1
            metrics.last_active = datetime.utcnow()
        
        # Update room membership
        membership = RoomMembership.query.filter_by(user_id=current_user.id, room_id=room.id).first()
        if membership:
            membership.is_active = True
            membership.last_active = datetime.utcnow()
        
        db.session.commit()
        
        # Get active members
        active_members = [m.user.username for m in room.memberships.filter_by(is_active=True).all()]
        
        # Notify others
        emit('user_joined', {
            'username': current_user.username,
            'active_members': active_members
        }, room=str(room.id))

@socketio.on('message')
def handle_message(data):
    """Handle incoming chat messages."""
    if not current_user.is_authenticated:
        return
    
    room_id = data.get('room_id')
    content = data.get('content', '').strip()
    
    if not room_id or not content:
        return
    
    room = Room.query.get(room_id)
    if not room:
        return

    # Check message content
    is_appropriate, warning = check_message(content)
    if not is_appropriate:
        emit('moderation_warning', {
            'message': warning
        }, room=request.sid)
        return
    
    try:
        # Create and save message
        message = Message(
            content=content,
            author=current_user,
            room=room,
            timestamp=datetime.utcnow()
        )
        db.session.add(message)
        db.session.commit()
        
        # Emit message to room
        emit('message', {
            'id': message.id,
            'content': message.content,
            'username': current_user.username,
            'user_id': current_user.id,
            'timestamp': message.timestamp.strftime('%H:%M'),
            'room_id': str(room_id)
        }, room=str(room_id))
        
    except Exception as e:
        db.session.rollback()
        emit('error', {
            'message': 'Failed to send message. Please try again.'
        }, room=request.sid)

@socketio.on('answer')
def handle_answer(data):
    """Handle answers to questions."""
    if not current_user.is_authenticated:
        return
    
    content = data.get('content')
    question_id = data.get('question_id')
    room_id = data.get('room_id')
    
    if not content or not question_id or not room_id:
        emit('error', {'message': 'Invalid answer data'}, room=request.sid)
        return
    
    question = Message.query.get(question_id)
    if not question or not question.is_question:
        emit('error', {'message': 'Invalid question'}, room=request.sid)
        return
        
    # Check if question already has an accepted answer
    if question.accepted_answer_id:
        emit('error', {'message': 'This question already has an accepted answer'}, room=request.sid)
        return
    
    # Create answer
    try:
        answer = Message(
            content=content,
            author=current_user,
            room_id=room_id,
            parent_id=question_id,
            timestamp=datetime.utcnow()
        )
        
        # Analyze answer content
        from app.text_analysis import text_analyzer
        analysis = text_analyzer.analyze_message(content)
        
        # Update answer with analysis results
        answer.primary_emotion = analysis['emotions']['primary_emotion']
        answer.emotion_score = analysis['emotions']['emotion_score']
        answer.all_emotions = json.dumps(analysis['emotions']['all_emotions'])
        answer.intent = 'answer'  # Override intent for answers
        answer.intent_confidence = 1.0
        
        db.session.add(answer)
        
        # Update question's answers count if needed
        question.answer_count = question.answer_count + 1 if hasattr(question, 'answer_count') else 1
        
        db.session.commit()
        
        # Emit answer to room
        emit('message', {
            'id': answer.id,
            'content': answer.content,
            'username': current_user.username,
            'user_id': current_user.id,
            'timestamp': answer.timestamp.strftime('%H:%M'),
            'room_id': str(room_id),
            'intent': answer.intent,
            'intent_emoji': '💡',  # Special emoji for answers
            'primary_emotion': answer.primary_emotion,
            'emotion_emoji': analysis['emotions'].get('emoji', '😐'),
            'parent_id': question_id,
            'is_answer': True,
            'accepted_answer_id': None,
            'question_content': question.content[:50] + ('...' if len(question.content) > 50 else '')
        }, room=str(room_id))
        
        # Notify question author
        if question.user_id != current_user.id:
            emit('new_answer', {
                'question_id': question_id,
                'answer_id': answer.id,
                'answerer': current_user.username
            }, room=str(question.user_id))
            
    except Exception as e:
        db.session.rollback()
        emit('error', {'message': 'Failed to submit answer. Please try again.'}, room=request.sid)
        print(f"Error in handle_answer: {str(e)}")  # Log the error

@socketio.on('accept_answer')
def handle_accept_answer(data):
    """Handle accepting an answer."""
    if not current_user.is_authenticated:
        return
    
    answer_id = data.get('answer_id')
    if not answer_id:
        emit('error', {'message': 'Invalid answer ID'}, room=request.sid)
        return
    
    answer = Message.query.get(answer_id)
    if not answer or not answer.parent_id:
        emit('error', {'message': 'Invalid answer'}, room=request.sid)
        return
    
    question = answer.parent_message
    if question.user_id != current_user.id:
        emit('error', {'message': 'Only the question author can accept answers'}, room=request.sid)
        return
    
    if question.accepted_answer_id:
        emit('error', {'message': 'An answer has already been accepted'}, room=request.sid)
        return
    
    # Accept the answer and transfer points
    if question.accept_answer(answer_id, db.session):
        # Notify answerer of points received
        emit('points_update', {
            'points': answer.author.points
        }, room=str(answer.author.id))
        
        # Notify room of accepted answer
        emit('answer_accepted', {
            'answer_id': answer_id,
            'question_id': question.id,
            'points_transferred': question.points_offered
        }, room=str(question.room_id))
    else:
        emit('error', {'message': 'Failed to accept answer'}, room=request.sid)

@socketio.on('rate_answer')
def handle_rating(data):
    """Handle rating an accepted answer."""
    if not current_user.is_authenticated:
        return
    
    message_id = data.get('message_id')
    rating_value = data.get('rating')
    
    if not message_id or not rating_value:
        emit('error', {'message': 'Invalid rating data'}, room=request.sid)
        return
    
    message = Message.query.get(message_id)
    if not message:
        emit('error', {'message': 'Invalid message'}, room=request.sid)
        return
    
    # Create or update rating
    rating = Rating(
        rater_id=current_user.id,
        rated_user_id=message.user_id,
        message_id=message_id,
        rating=rating_value
    )
    
    if not rating.can_rate():
        emit('error', {'message': 'Cannot rate this answer'}, room=request.sid)
        return
    
    try:
        db.session.add(rating)
        message.author.update_rating(rating_value)
        db.session.commit()
        
        emit('rating_updated', {
            'message_id': message_id,
            'new_rating': message.author.rating
        }, room=str(message.room_id))
    except Exception as e:
        db.session.rollback()
        emit('error', {'message': 'Failed to submit rating'}, room=request.sid)

@socketio.on('leave')
def on_leave(data):
    """Handle user leaving a chat room."""
    room_id = data.get('room_id')
    if room_id:
        leave_room(str(room_id))
        
        # Update room membership
        membership = RoomMembership.query.filter_by(user_id=current_user.id, room_id=room_id).first()
        if membership:
            membership.is_active = False
            db.session.commit()
            
            # Get remaining active members
            room = Room.query.get(room_id)
            if room:
                active_members = [m.user.username for m in room.memberships.filter_by(is_active=True).all()]
                
                # Notify others
                emit('user_left', {
                    'username': current_user.username,
                    'active_members': active_members
                }, room=str(room_id)) 