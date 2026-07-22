# Firebase Realtime Database functions
# All data is stored in Firebase - no SQL database needed!

from datetime import datetime

def save_chat_history(firebase, user_uid, user_email, question, answer):
    """Save chat to Firebase Realtime Database under user-specific path"""
    db = firebase.database()
    timestamp = datetime.utcnow().isoformat()
    
    chat_data = {
        "user_email": user_email,
        "question": question,
        "answer": answer,
        "timestamp": timestamp
    }
    
    try:
        # Save to /user_chats/{user_uid} using a chronological push ID
        db.child("user_chats").child(user_uid).push(chat_data)
        return True
    except Exception as e:
        print(f"Error saving chat: {e}")
        return False

def get_user_chat_history(firebase, user_uid):
    """Get all chats for a specific user directly from Firebase"""
    db = firebase.database()
    
    try:
        chats = db.child("user_chats").child(user_uid).get()
        if chats.val():
            # Convert to list and sort by timestamp (newest first)
            chat_list = []
            for key, val in chats.val().items():
                val['id'] = key
                chat_list.append(val)
            return sorted(chat_list, key=lambda x: x.get('timestamp', ''), reverse=True)
        return []
    except Exception as e:
        print(f"Error retrieving chats: {e}")
        return []

def get_total_chats(firebase, user_uid):
    """Get total number of chats for a user"""
    chats = get_user_chat_history(firebase, user_uid)
    return len(chats)