# ABOUTME: Application phase for the batch quiz upgrade.
# ABOUTME: Patches HTML files with verified AI-generated facts and follow-up Q&A.

import json
import os
import sys
import logging
import re
from pathlib import Path
from bs4 import BeautifulSoup

# Add page-generator to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from batch.utils import StateManager
import fact_verifier

def patch_html(html_content, new_data, player_name):
    """
    Surgically updates the HTML content with new facts and follow-up Q&A.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. Update facts <ul> in .player-info
    player_info = soup.select_one('.player-info')
    if player_info:
        ul = player_info.find('ul')
        if not ul:
            ul = soup.new_tag('ul')
            player_info.append(ul)
            
        ul.clear()
        for fact in new_data.get('facts', []):
            li = soup.new_tag('li')
            li.string = fact
            ul.append(li)
    
    # 2. Inject/Replace followup-section
    followup_section = soup.find(id='followup-section')
    if not followup_section and player_info:
        # Create it if it doesn't exist
        followup_section = soup.new_tag('div', id='followup-section', attrs={'class': 'followup-section'})
        player_info.append(followup_section)
    
    if followup_section:
        followup_section.clear()
        h3 = soup.new_tag('h3')
        h3.string = f"Would you like to find out more about {player_name}?"
        followup_section.append(h3)
        
        buttons_div = soup.new_tag('div', attrs={'class': 'followup-buttons'})
        for qa in new_data.get('qa', []):
            item_div = soup.new_tag('div', attrs={'class': 'followup-item'})
            btn = soup.new_tag('button', attrs={
                'class': 'followup-btn',
                'data-answer': qa.get('answer', '')
            })
            btn.string = qa.get('question', '')
            item_div.append(btn)
            
            answer_div = soup.new_tag('div', attrs={'class': 'followup-answer', 'style': 'display:none;'})
            item_div.append(answer_div)
            
            buttons_div.append(item_div)
        followup_section.append(buttons_div)

    # 3. Update #quiz-data JSON
    quiz_data_el = soup.find(id='quiz-data')
    if quiz_data_el:
        try:
            # Try to preserve existing fields like 'answer'
            content = quiz_data_el.string if quiz_data_el.name == 'script' else quiz_data_el.get_text()
            existing_json = json.loads(content)
        except Exception:
            existing_json = {}
        
        # Standardize on 'hints' as per existing files, but also include 'facts' for the test
        existing_json['hints'] = new_data.get('facts', [])
        existing_json['facts'] = new_data.get('facts', [])
        
        new_json_str = json.dumps(existing_json, indent=4)
        if quiz_data_el.name == 'script':
            quiz_data_el.string = new_json_str
        else:
            # For div, we want to maintain the style if possible, but at least valid JSON
            quiz_data_el.string = f"\n{new_json_str}\n"

    # 4. Add the JS handler for the followup buttons if missing
    if not soup.find('script', string=re.compile('followup-btn')):
        js_handler = """
    document.addEventListener('DOMContentLoaded', function() {
        const container = document.getElementById('followup-section');
        if (!container) return;
        const items = container.querySelectorAll('.followup-item');
        if (!items.length) return;

        items.forEach(function(item) {
            const btn = item.querySelector('.followup-btn');
            const answerBox = item.querySelector('.followup-answer');
            if (!btn || !answerBox) return;

            btn.addEventListener('click', function() {
                const answer = btn.getAttribute('data-answer') || '';
                if (!answer) return;

                // Toggle visibility
                const isHidden = answerBox.style.display === 'none' || !answerBox.style.display;
                if (isHidden) {
                    answerBox.textContent = answer;
                    answerBox.style.display = 'block';
                } else {
                    answerBox.style.display = 'none';
                }
            });
        });
    });
    """
        new_script = soup.new_tag('script')
        new_script.string = js_handler
        # Insert before footer or at end of body
        footer = soup.find('footer')
        if footer:
            footer.insert_before(new_script)
        else:
            soup.body.append(new_script)

    return soup.prettify() if not html_content.strip().startswith('<!DOCTYPE') else str(soup)

def main(project_root):
    root_path = Path(project_root)
    state_file = root_path / "page-generator" / "batch" / "state.json"
    responses_file = root_path / "temp" / "responses.jsonl"
    dossier_dir = root_path / "temp" / "dossiers"
    audit_report_path = root_path / "FACT_AUDIT_REPORT.md"
    
    manager = StateManager(state_file)
    
    if not responses_file.exists():
        print(f"Responses file not found: {responses_file}")
        return

    with open(responses_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            
            try:
                resp_data = json.loads(line)
            except json.JSONDecodeError:
                print(f"Failed to parse JSON line: {line}")
                continue
            
            try:
                content_text = ""
                # Developer API structure: {"response": {"candidates": [{"content": {"parts": [{"text": "..."}]}}]}}
                response_obj = resp_data.get('response', {})
                body = response_obj.get('body', {})
                candidates = body.get('candidates', []) if body else response_obj.get('candidates', [])
                if candidates:
                    content_text = candidates[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                
                if not content_text:
                    print("Could not extract content for a response line.")
                    continue
                
                # Parse the JSON from the text
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', content_text, re.DOTALL)
                if json_match:
                    content_json = json.loads(json_match.group(1))
                else:
                    # Try cleaning common AI fluff if it's not in a code block
                    cleaned_text = re.sub(r'^[^{]*', '', content_text)
                    cleaned_text = re.sub(r'[^}]*$', '', cleaned_text)
                    content_json = json.loads(cleaned_text)
                
                # Identify the date from the JSON content
                date_str = content_json.get('date')
                if not date_str:
                    print("Could not find date in response content.")
                    continue
                
                # Load dossier
                dossier_path = dossier_dir / f"{date_str}.json"
                if not dossier_path.exists():
                    print(f"Dossier not found for {date_str}")
                    continue
                
                with open(dossier_path, 'r', encoding='utf-8') as df:
                    dossier = json.load(df)
                
                # Verify claims
                claims = content_json.get('claims', [])
                if fact_verifier.verify_claims(claims, dossier):
                    # Patch HTML
                    html_file = root_path / f"{date_str}.html"
                    if html_file.exists():
                        with open(html_file, 'r', encoding='utf-8') as hf:
                            old_html = hf.read()
                        
                        player_name = manager.get_data(date_str).get('player', date_str)
                        updated_html = patch_html(old_html, content_json, player_name)
                        
                        with open(html_file, 'w', encoding='utf-8') as hf:
                            hf.write(updated_html)
                        
                        manager.set_status(date_str, "completed")
                        print(f"Successfully updated {date_str}")
                    else:
                        print(f"HTML file not found: {html_file}")
                else:
                    # Verification failed
                    manager.set_status(date_str, "failed")
                    with open(audit_report_path, 'a', encoding='utf-8') as af:
                        af.write(f"## {date_str} - {dossier.get('name')}\n")
                        af.write("Fact verification failed for the following claims:\n")
                        for claim in claims:
                            af.write(f"- {claim}\n")
                        af.write("\n")
                    print(f"Fact verification failed for {date_str}")
                
                manager.save()
                
            except Exception as e:
                print(f"Error processing {date_str}: {e}")

if __name__ == "__main__":
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    main(project_root)
