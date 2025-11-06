import logging
import re
from typing import Optional, Tuple
from word2number import w2n

logger = logging.getLogger(__name__)

class CommandParser:
    def __init__(self):
        # Define command patterns for elderly speech variations
        self.patterns = {
            'set_task': [
                r'(?:remind me to|set task for|i need to) (.+?) (?:at|on|by)\s*(.+)',
                r'(?:remember|task) (.+?) (?:at|on|by)\s*(.+)',
                r'(?:i have to|i must) (.+?) (?:at|on|by)\s*(.+)',
                r'remind me (.+?) (?:at|on|by)\s*(.+)',
                r'(.+?) (?:at|on|by)\s*(.+)',
                r'(?:don\'t forget to|please remember to) (.+?) (?:at|on|by)\s*(.+)',
            ],
            'relative_time': [
                r'(.+?) (?:in|after) (\d+) (minute|hour)s?',
                r'(?:remind me to|set task for) (.+?) (?:in|after) (\d+) (minute|hour)s?',
            ],
            'list_tasks': [
                r'(?:show|list|tell|read|what are) (?:my|the) tasks?',
                r'(?:what do i have|what\'s) scheduled?',
            ],
            'delete_task': [
                r'(?:delete|forget about|cancel) (?:the )?task (?:for )?(.+)',
                r'(?:delete|remove|cancel) (.+) task',
            ]
        }

    def parse_task_command(self, text: str) -> Optional[dict]:
        """Always return dict with consistent structure"""
        text = text.lower().strip()
        logger.info(f"Parsing command: '{text}'")

        # 1. DELETE commands (HIGHEST PRIORITY)
        delete_result = self._parse_delete_command(text)
        if delete_result:
            command_type, task_desc = delete_result
            formatted_task = self.format_task_text(task_desc)
            return {"type": command_type, "task": formatted_task}

        # 2. LIST commands
        if self._is_list_tasks_command(text):
            return {"type": "LIST_TASKS"}

        # 3. ADD commands (LOWEST PRIORITY)
        for pattern in self.patterns['set_task']:
            match = re.search(pattern, text)
            if match:
                # Handle different group patterns
                if len(match.groups()) == 2:
                    task = match.group(1).strip()
                    time_text = match.group(2).strip()
                else:
                    task = match.group(-2).strip()
                    time_text = match.group(-1).strip()

                # Apply sentence case formatting
                formatted_task = self.format_task_text(task)
                normalized_time = self._normalize_time_ampm(time_text)
                
                if normalized_time:
                    logger.info(f"Parsed: task='{formatted_task}', time='{normalized_time}'")
                    return {
                        "type": "ADD_TASK", 
                        "task": formatted_task, 
                        "time": normalized_time
                    }

        logger.warning(f"No valid pattern matched for: {text}")
        return None

    def _parse_delete_command(self, text: str) -> Optional[Tuple[str, str]]:
        """Parse delete task command - returns tuple for internal use"""
        for pattern in self.patterns['delete_task']:
            match = re.search(pattern, text)
            if match:
                task_to_delete = match.group(1).strip()
                logger.info(f"Parsed delete command for: '{task_to_delete}'")
                return "DELETE_TASK", task_to_delete
        return None

    def _is_list_tasks_command(self, text: str) -> bool:
        """Check if the command is asking to list tasks"""
        for pattern in self.patterns['list_tasks']:
            if re.search(pattern, text):
                return True
        return False

    def _parse_relative_time(self, text: str) -> Optional[Tuple[str, str]]:
        """Parse relative time commands (in X minutes/hours)"""
        for pattern in self.patterns['relative_time']:
            match = re.search(pattern, text)
            if match:
                # Handle different group patterns
                if len(match.groups()) == 3:
                    task = match.group(1).strip()
                    amount = int(match.group(2))
                    unit = match.group(3)
                else:
                    task = match.group(1).strip()
                    amount = int(match.group(2))
                    unit = match.group(3)

                relative_time = self._calculate_relative_time(amount, unit)
                if relative_time:
                    logger.info(f"Parsed relative time: task='{task}', time='{relative_time}'")
                    return task, relative_time
        return None

    def format_task_text(self, text: str) -> str:
        """Format task text to proper sentence case for BOTH screens"""
        if not text or not text.strip():
            return text
        
        text = text.strip()
        
        # Common nouns and proper nouns to capitalize
        nouns_to_capitalize = {
            'doctor', 'nurse', 'hospital', 'pharmacy', 'medicine', 'pill', 
            'tablet', 'dose', 'appointment', 'clinic', 'emergency',
            'son', 'daughter', 'wife', 'husband', 'mother', 'father',
            'mom', 'dad', 'grandpa', 'grandma', 'family', 'love'
        }
        
        # Action verbs to capitalize  
        action_verbs = {
            'call', 'take', 'visit', 'see', 'meet', 'schedule', 'book',
            'remember', 'remind', 'check', 'monitor', 'measure', 'walk',
            'exercise', 'eat', 'drink', 'read', 'write'
        }
        
        # Proper names (common first names)
        proper_names = {
            'james', 'john', 'mary', 'sarah', 'michael', 'david', 'lisa',
            'anna', 'paul', 'peter', 'robert', 'william', 'elizabeth'
        }
        
        words = text.split()
        formatted_words = []
        
        for i, word in enumerate(words):
            clean_word = word.lower().strip('.,!?')
            
            # Always capitalize first word
            if i == 0:
                formatted_word = word[0].upper() + word[1:].lower() if len(word) > 1 else word.upper()
            # Capitalize nouns, action verbs, and proper names
            elif (clean_word in nouns_to_capitalize or 
                  clean_word in action_verbs or 
                  clean_word in proper_names):
                formatted_word = word[0].upper() + word[1:].lower() if len(word) > 1 else word.upper()
            # Keep articles/prepositions lowercase
            else:
                formatted_word = word.lower()
            
            formatted_words.append(formatted_word)
        
        return ' '.join(formatted_words)

    def _normalize_time_ampm(self, time_text: str) -> Optional[str]:
        """Normalize time text to AM/PM format only"""
        time_text = time_text.lower().strip()
        logger.debug(f"Normalizing time to AM/PM: {time_text}")

        # Handle special cases
        if 'noon' in time_text or 'midday' in time_text:
            return '12:00 PM'
        elif 'midnight' in time_text:
            return '12:00 AM'

        # Try word-to-number conversion for all number words
        try:
            # Convert common number words in the entire time text
            words = time_text.split()
            converted_words = []
            for word in words:
                try:
                    if word in ['am', 'pm', 'a.m', 'p.m', 'a.m.', 'p.m.', 'morning', 'evening', 'night']:
                        converted_words.append(word)
                        continue

                    # Try to convert word to number
                    num = w2n.word_to_num(word)
                    if 1 <= num <= 12:
                        converted_words.append(str(num))
                    else:
                        converted_words.append(word)
                except ValueError:
                    converted_words.append(word)

            time_text = ' '.join(converted_words)
            logger.debug(f"After word-to-number conversion: {time_text}")
        except Exception as e:
            logger.debug(f"Word-to-number conversion failed: {e}")

        # Enhanced time patterns that handle various formats
        time_patterns = [
            # Handle "10 p m" format (spaces between letters)
            r'(\d{1,2})\s+(p\s*m|a\s*m|p\.\s*m|a\.\s*m)',
            # Handle "10 pm" format
            r'(\d{1,2})\s*(pm|am|p\.m|a\.m|p\. m|a\. m)',
            # Handle "10:30 pm" format
            r'(\d{1,2}):(\d{2})\s*(pm|am|p\.m|a\.m)',
            # Handle "10 o'clock pm" format
            r'(\d{1,2})\s*o\'?clock\s*(pm|am|p\.m|a\.m)?',
            # Handle simple hour with context
            r'^(\d{1,2})$',
            # Handle 24-hour format
            r'(\d{1,2}):(\d{2})',
        ]

        for pattern in time_patterns:
            match = re.search(pattern, time_text, re.IGNORECASE)
            if match:
                groups = match.groups()
                logger.debug(f"Matched pattern '{pattern}' with groups: {groups}")

                hour = int(groups[0])
                minute = '00'
                period = ''

                # Extract minute if available
                if len(groups) >= 2 and groups[1] and groups[1].isdigit():
                    minute = groups[1]
                elif len(groups) >= 2 and groups[1] and any(x in groups[1].lower() for x in ['p', 'a']):
                    # Handle case where second group is period indicator
                    period = groups[1]
                elif len(groups) >= 3 and groups[2]:
                    period = groups[2]

                # Clean up period indicator
                if period:
                    period = 'PM' if 'p' in period.lower() else 'AM'
                else:
                    # Determine period from context
                    if 'evening' in time_text or 'night' in time_text or 'p' in time_text:
                        period = 'PM'
                    elif 'morning' in time_text or 'a' in time_text:
                        period = 'AM'
                    else:
                        # Default logic for simple hours
                        if 1 <= hour <= 11:
                            period = 'AM'
                        elif hour == 12:
                            period = 'PM'
                        else:
                            period = 'PM'

                # Handle 24-hour format conversion
                if pattern == r'(\d{1,2}):(\d{2})' and len(groups) == 2:
                    # This is a 24-hour format, convert to 12-hour
                    return self._convert_24_to_12_hour(hour, minute)

                # Handle 12-hour format boundaries
                if hour > 12:
                    hour = hour - 12
                    period = 'PM'
                elif hour == 0:
                    hour = 12
                    period = 'AM'

                # Ensure hour is valid
                if hour < 1 or hour > 12:
                    continue

                normalized_time = f"{hour}:{minute} {period}"
                logger.debug(f"Normalized '{time_text}' to '{normalized_time}'")
                return normalized_time

        logger.warning(f"Could not parse time: {time_text}")
        return None

    def _convert_24_to_12_hour(self, hour: int, minute: str) -> str:
        """Convert 24-hour format to 12-hour AM/PM format"""
        if hour == 0:
            return f"12:{minute} AM"
        elif hour == 12:
            return f"12:{minute} PM"
        elif hour > 12:
            return f"{hour - 12}:{minute} PM"
        else:
            return f"{hour}:{minute} AM"

    def _calculate_relative_time(self, amount: int, unit: str) -> str:
        """Calculate relative time and return in AM/PM format"""
        from datetime import datetime, timedelta

        now = datetime.now()
        if unit.startswith('minute'):
            future = now + timedelta(minutes=amount)
        elif unit.startswith('hour'):
            future = now + timedelta(hours=amount)
        else:
            return None

        # Convert to 12-hour AM/PM format
        hour = future.hour
        minute = future.minute

        if hour == 0:
            return f"12:{minute:02d} AM"
        elif hour == 12:
            return f"12:{minute:02d} PM"
        elif hour > 12:
            return f"{hour - 12}:{minute:02d} PM"
        else:
            return f"{hour}:{minute:02d} AM"