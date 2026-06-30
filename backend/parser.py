import re
from datetime import datetime

def parse_whatsapp_chat(filepath: str, chat_name: str = "Unknown Chat", chat_mode: str = "group") -> dict:
    """
    Parses a WhatsApp exported .txt file purely in-memory.
    Returns a dictionary containing chat metadata and a list of message dicts.
    """
    # Pattern to match WhatsApp lines: DD/MM/YY, HH:MM [am/pm] - Sender: Message
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
                    dt = datetime.strptime(dt_str, "%d/%m/%y %I:%M %p")
                except ValueError:
                    try:
                        dt = datetime.strptime(dt_str, "%d/%m/%y %H:%M")
                    except ValueError:
                        try:
                            dt = datetime.strptime(dt_str, "%d/%m/%Y %H:%M")
                        except ValueError:
                            dt = datetime.now()
                
                # Determine if it's a user message or a system message
                if ':' in content:
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
            
    return {
        "chat_name": chat_name,
        "chat_mode": chat_mode,
        "messages": messages
    }
