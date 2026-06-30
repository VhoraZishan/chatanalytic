import re
from datetime import datetime
try:
    from backend.database import get_db_connection
except ImportError:
    from database import get_db_connection

def parse_whatsapp_chat(filepath: str, chat_name: str = "Unknown Chat", chat_mode: str = "group"):
    """
    Parses a WhatsApp exported .txt file and saves it to the local SQLite database.
    Returns the chat_id of the newly inserted chat.
    """
    # Pattern to match WhatsApp lines: DD/MM/YY, HH:MM [am/pm] - Sender: Message
    # Handles variations like non-breaking spaces (\u202f) in am/pm
    pattern = re.compile(r'^(\d{2}/\d{2}/\d{2,4}),\s*(\d{1,2}:\d{2}\s*[a-zA-Z\u202f]*)\s*-\s*(.*?)$')
    
    messages = []
    current_msg = None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            match = pattern.match(line)
            if match:
                date_str, time_str, content = match.groups()
                
                # Normalize time string to parse correctly
                dt_str = f"{date_str} {time_str}".replace('\u202f', ' ').replace('\u2028', '').strip()
                try:
                    # 12-hour format: 04/09/25 9:39 am
                    dt = datetime.strptime(dt_str, "%d/%m/%y %I:%M %p")
                except ValueError:
                    try:
                        # 24-hour format: 04/09/25 14:39
                        dt = datetime.strptime(dt_str, "%d/%m/%y %H:%M")
                    except ValueError:
                        # Fallback for 4-digit years
                        try:
                            dt = datetime.strptime(dt_str, "%d/%m/%Y %H:%M")
                        except ValueError:
                            dt = datetime.now()
                
                # Determine if it's a user message or a system message
                if ':' in content:
                    # Split only on the first colon to get sender
                    sender, text = content.split(':', 1)
                    sender = sender.strip()
                    text = text.strip()
                    
                    if text == '<Media omitted>':
                        msg_type = 'media'
                    elif text == 'This message was deleted':
                        msg_type = 'deleted'
                    else:
                        msg_type = 'text'
                else:
                    # System event (e.g., "X created group Y", "Messages are end-to-end encrypted")
                    sender = "SYSTEM"
                    text = content
                    msg_type = 'system'
                    
                if current_msg:
                    messages.append(current_msg)
                    
                current_msg = {
                    'timestamp': dt,
                    'sender': sender,
                    'text': text,
                    'type': msg_type
                }
            else:
                # Continuation of previous multi-line message
                if current_msg:
                    current_msg['text'] += f"\n{line}"
                    
        if current_msg:
            messages.append(current_msg)
            
    return _save_to_db(chat_name, messages, chat_mode)

def _save_to_db(chat_name, messages, chat_mode: str = "group"):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Create chat record
        cursor.execute("INSERT INTO chats (name, chat_mode) VALUES (?, ?)", (chat_name, chat_mode))
        chat_id = cursor.lastrowid
        
        # 2. Extract and insert unique participants
        unique_senders = set(m['sender'] for m in messages if m['sender'] != "SYSTEM")
        sender_ids = {}
        for sender in unique_senders:
            cursor.execute(
                "INSERT INTO participants (chat_id, display_name, normalized_name) VALUES (?, ?, ?)",
                (chat_id, sender, sender.lower().strip())
            )
            sender_ids[sender] = cursor.lastrowid
            
        # 3. Insert messages
        for m in messages:
            s_id = sender_ids.get(m['sender']) # Will be None for SYSTEM messages
            cursor.execute(
                "INSERT INTO messages (chat_id, sender_id, timestamp, text, message_type) VALUES (?, ?, ?, ?, ?)",
                (chat_id, s_id, m['timestamp'], m['text'], m['type'])
            )
            
        conn.commit()
        return chat_id

if __name__ == "__main__":
    # Simple manual test block
    import os
    base_dir = os.path.dirname(os.path.dirname(__file__))
    test_file = os.path.join(base_dir, "chat", "WhatsApp Chat with Team Work.txt")
    
    if os.path.exists(test_file):
        print(f"Parsing {test_file}...")
        chat_id = parse_whatsapp_chat(test_file, "Team Work Test")
        print(f"Successfully parsed! Inserted as chat_id: {chat_id}")
        
        # Verify
        with get_db_connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM messages WHERE chat_id = ?", (chat_id,)).fetchone()[0]
            print(f"Total messages inserted: {count}")
    else:
        print(f"File not found: {test_file}")
