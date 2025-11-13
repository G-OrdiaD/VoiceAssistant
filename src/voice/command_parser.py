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
                r'^(?:delete|remove|cancel|clear|erase)\s+(?:the\s*)?(?:task\s*)?(.*?)(?:\s+(?:at|on|by|for)\s+.+)?$',
                r'(?:delete|forget about|cancel) (?:the )?task (?:for )?(.+)',
                r'(?:delete|remove|cancel) (.+) task',
                r'^(?:delete|remove|cancel) (?:my |the )?(.+)$',
                r'^(?:forget about|don\'t remind me about) (.+)$',
                r'^(?:clear|erase) (.+)$',
                r'^(?:delete|remove|cancel) (.+?) (?:at|on|by|for) .+$',
            ],
            'mark_done': [
                r'^(?:done with|completed|finished) (?:my |the )?(.+)$',
                r'^(?:mark|set) (.+) as done$',
                r'^(?:task|reminder) (.+) (?:is |are )?(?:done|completed)$',
            ]
        }

    def parse_task_command(self, text: str) -> Optional[dict]:
        """Always return dict with consistent structure"""
        text = text.lower().strip()
        logger.info(f"Parsing command: '{text}'")

        # 1. DELETE commands (strict precedence)
        delete_result = self._parse_delete_command(text)
        if delete_result:
            return delete_result

        # Guard: if it clearly starts with a delete-type verb but none of the
        # specific patterns matched, treat as DELETE with a best-effort target
        if self._looks_like_delete(text):
            fallback = self._fallback_delete(text)
            if fallback:
                return fallback

        # 2. MARK DONE commands
        done_result = self._parse_mark_done_command(text)
        if done_result:
            return done_result

        # 3. LIST commands
        if self._is_list_tasks_command(text):
            return {"type": "LIST_TASKS"}

        # 4. RELATIVE TIME commands
        relative_result = self._parse_relative_time(text)
        if relative_result:
            task, time = relative_result
            formatted_task = self.format_task_text(task)
            return {"type": "ADD_TASK", "task": formatted_task, "time": time}

        # 5. ADD commands
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

    def _parse_delete_command(self, text: str) -> Optional[dict]:
        """Parse delete task command - returns formatted dict"""
        for pattern in self.patterns['delete_task']:
            match = re.search(pattern, text)
            if match:
                task_to_delete = match.group(1).strip()
                # Clean trivial fillers like 'task', 'my task', etc.
                task_to_delete = re.sub(r'^(?:my|the)\s+task\s*', '', task_to_delete).strip()
                task_to_delete = re.sub(r'^\btask\b\s*', '', task_to_delete).strip()
                if not task_to_delete:
                    # If we end up with empty (e.g., "delete task"), keep as-is to let caller handle
                    task_to_delete = 'task'
                formatted_task = self.format_task_text(task_to_delete)
                logger.info(f"Parsed delete command for: '{formatted_task}'")
                return {"type": "DELETE_TASK", "task": formatted_task}
        return None

    def _looks_like_delete(self, text: str) -> bool:
        """Heuristic: starts with a delete-type verb ⇒ do not allow fall-through to ADD."""
        return bool(re.match(r'^(?:delete|remove|cancel|clear|erase|forget(?: about)?)\b', text))

    def _fallback_delete(self, text: str) -> Optional[dict]:
        """
        Best-effort extraction for delete if explicit patterns didn’t match.
        Strips leading delete-verb and trailing time clause.
        """
        # Drop leading verb
        m = re.match(r'^(?:delete|remove|cancel|clear|erase|forget(?: about)?)\s+(.*)$', text)
        if not m:
            return None
        core = m.group(1).strip()

        # Remove common fillers like "the task", "my task"
        core = re.sub(r'^(?:the|my)\s+task\s*', '', core).strip()
        core = re.sub(r'^\btask\b\s*', '', core).strip()

        # Strip trailing time clause: "at/on/by/for …"
        core = re.sub(r'\s+(?:at|on|by|for)\s+.*$', '', core).strip()

        if not core:
            core = 'task'
        formatted = self.format_task_text(core)
        logger.info(f"Fallback delete target: '{formatted}'")
        return {"type": "DELETE_TASK", "task": formatted}

    def _parse_mark_done_command(self, text: str) -> Optional[dict]:
        """Parse mark as done commands"""
        for pattern in self.patterns['mark_done']:
            match = re.search(pattern, text)
            if match:
                task_to_mark = match.group(1).strip()
                formatted_task = self.format_task_text(task_to_mark)
                logger.info(f"Parsed mark done command for: '{formatted_task}'")
                return {"type": "MARK_DONE", "task": formatted_task}
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
