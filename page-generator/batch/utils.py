# ABOUTME: Core utilities and state management for batch quiz processing.
# ABOUTME: Tracks progress and player data across multiple execution phases.

import json
from pathlib import Path

class StateManager:
    def __init__(self, path):
        self.path = Path(path)
        self.state = {}
        if self.path.exists():
            with open(self.path, 'r') as f:
                try:
                    self.state = json.load(f)
                except json.JSONDecodeError:
                    self.state = {}
                
    def get_status(self, date):
        entry = self.state.get(date, {})
        return entry.get("status")
        
    def get_data(self, date):
        return self.state.get(date, {}).get("data", {})
        
    def set_status(self, date, status, data=None):
        if date not in self.state:
            self.state[date] = {}
        self.state[date]["status"] = status
        if data:
            self.state[date]["data"] = data
            
    def save(self):
        temp_path = self.path.with_suffix(".tmp")
        with open(temp_path, 'w') as f:
            json.dump(self.state, f, indent=2)
        temp_path.replace(self.path)

BATCH_PROMPT_TEMPLATE = """
You are a "Skeptical Storyteller" tasked with generating high-accuracy, engaging trivia for a New York Yankees trivia game.
Your goal is to generate trivia "hints" and "follow-up stories" about the player: {name}.

**PLAYER DOSSIER**:
{dossier_json}

**STRICT RULES**:
1. **NO NAME IN HINTS**: You MUST NEVER use the player's name ({name}) or his nickname in the hints. Refer to him as "this player", "the reliever", etc.
2. **AVOID GIF REPETITION**: The user can already see the player's team list and years (e.g. "NYY 1974-1976") in a GIF. DO NOT simply repeat his tenure or team sequence in the hints.
3. **STORY-DRIVEN**: Use the SABR biography to find interesting anecdotes, weird circumstances, or defining moments.
4. **STRICT GROUNDING**: ONLY use info in the dossier. If you include a year or stat, it must be verbatim from the dossier.

**TASK 1: HINTS (The "facts" list)**
Generate exactly 3 trivia hints. These should be progressively easier. 
- Hint 1: An obscure or early career detail (e.g. college, draft, or a weird minor league story).
- Hint 2: A notable milestone, award, or unique narrative detail (e.g. a specific record or a famous play).
- Hint 3: A career-defining achievement or reputation-based fact (e.g. "Led the league in X", "World Series heroics", or "Known for his devastating curveball").
- **IMPORTANT**: Avoid just saying "He played for the Yankees from X to Y". The user already knows that!

**TASK 2: FOLLOW-UP STORIES (The "qa" list)**
Generate exactly 3 Q&A pairs that provide more depth for users who want to "find out more."
- These should reveal interesting narrative arcs.
- The answers should be 1-3 sentences and feel like a story.

**TASK 3: ATOMIC CLAIMS (The "claims" list)**
Extract ALL atomic factual statements (specific years, statistics, team names, awards) mentioned in your HINTS and FOLLOW-UP STORIES.
- Each claim should be a single, verifiable sentence.
- Example: "He won the Cy Young Award in 1978."
- Example: "He played for the Yankees from 1974 to 1976."

**OUTPUT FORMAT**:
Return ONLY a JSON object with the following structure:
{{
  "date": "{date_str}",
  "facts": ["hint 1", "hint 2", "hint 3"],
  "qa": [
    {{"question": "How did he...", "answer": "The player..."}},
    {{"question": "What happened...", "answer": "In 1974..."}},
    {{"question": "...", "answer": "..."}}
  ],
  "claims": ["claim 1", "claim 2", ...]
}}
"""
