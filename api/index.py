from flask import Flask, render_template, request, jsonify
import os
import sys

# Vercel-specific imports
app = Flask(__name__)

# Lightweight plagiarism detection for Vercel
class LightweightDetector:
    def __init__(self):
        self.suspicious_patterns = [
            r'\b(?:copy|copied|paste|pasted|copypaste)\b',
            r'\b(?:wikipedia|wiki)\b',
            r'\b(?:source|sources)\s*:',
            r'(?:retrieved|accessed)\s+(?:from|on)',
            r'\b(?:doi|isbn|url|http|https|www)\b',
            r'©|\bcopyright\b|\ball rights reserved\b',
            r'\[\d+\]|\(\d{4}\)',
            r'\bet al\b|\betal\b',
        ]
        
    def analyze_text(self, text):
        import re
        words = text.split()
        sentences = text.split('.')
        unique_words = len(set(words))
        
        # Simple plagiarism scoring
        score = 0
        issues = []
        
        # Check patterns
        suspicious_count = 0
        for pattern in self.suspicious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                suspicious_count += 1
        
        score += suspicious_count * 15
        
        # Check word diversity
        if len(words) > 0:
            unique_ratio = unique_words / len(words)
            if unique_ratio < 0.4:
                score += 25
                issues.append("Low vocabulary diversity detected")
        
        # Check sentence structure
        if len(sentences) > 1:
            avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
            if avg_length > 35:
                score += 20
                issues.append("Very long sentences detected")
        
        # Determine risk level
        if score >= 50:
            level = "High"
            color = "danger"
        elif score >= 25:
            level = "Medium" 
            color = "warning"
        else:
            level = "Low"
            color = "success"
            
        return {
            'plagiarism_score': min(score, 100),
            'plagiarism_level': level,
            'risk_color': color,
            'text_analysis': {
                'total_words': len(words),
                'unique_words': unique_words,
                'total_sentences': len(sentences)
            },
            'issues': issues,
            'suspicious_patterns': suspicious_count
        }

class LightweightRephraser:
    def __init__(self):
        # Compact synonym dictionary for Vercel
        self.synonyms = {
            'important': ['significant', 'crucial', 'vital', 'essential'],
            'big': ['large', 'huge', 'enormous', 'massive'],
            'good': ['excellent', 'outstanding', 'superior', 'remarkable'],
            'bad': ['poor', 'inferior', 'inadequate', 'deficient'],
            'show': ['demonstrate', 'illustrate', 'reveal', 'display'],
            'make': ['create', 'produce', 'generate', 'develop'],
            'use': ['utilize', 'employ', 'apply', 'implement'],
            'many': ['numerous', 'several', 'various', 'multiple'],
            'new': ['novel', 'recent', 'modern', 'contemporary'],
            'old': ['ancient', 'traditional', 'historical', 'vintage'],
            'very': ['extremely', 'highly', 'considerably', 'significantly'],
            'simple': ['basic', 'elementary', 'straightforward', 'plain'],
            'changed': ['altered', 'modified', 'transformed', 'revised'],
            'example': ['instance', 'illustration', 'sample', 'case'],
            'married': ['wed', 'united', 'joined', 'bonded'],
            'husband': ['spouse', 'partner', 'mate', 'companion'],
            'moved': ['relocated', 'transferred', 'shifted', 'traveled'],
            'young': ['youthful', 'juvenile', 'adolescent', 'tender']
        }
        
    def rephrase_text(self, text, style='academic', creativity='medium'):
        import random
        import re
        
        words = text.split()
        changes = []
        rephrased_words = []
        
        replacement_prob = 0.4 if creativity == 'low' else 0.6 if creativity == 'medium' else 0.8
        
        for i, word in enumerate(words):
            clean_word = re.sub(r'[^\w]', '', word.lower())
            
            if clean_word in self.synonyms and random.random() < replacement_prob:
                synonym = random.choice(self.synonyms[clean_word])
                # Preserve capitalization
                if word[0].isupper():
                    synonym = synonym.capitalize()
                rephrased_words.append(synonym)
                changes.append({
                    'original': word,
                    'replacement': synonym,
                    'position': i
                })
            else:
                rephrased_words.append(word)
        
        return ' '.join(rephrased_words), changes

# Initialize lightweight versions
detector = LightweightDetector()
rephraser = LightweightRephraser()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text.strip():
            return jsonify({'error': 'Text must be provided'}), 400
            
        if len(text.strip()) < 50:
            return jsonify({'error': 'Please provide at least 50 characters'}), 400
        
        result = detector.analyze_text(text)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': f'Analysis error: {str(e)}'}), 500

@app.route('/rephrase', methods=['POST'])
def rephrase():
    try:
        data = request.json
        text = data.get('text', '')
        style = data.get('style', 'academic')
        creativity = data.get('creativity', 'medium')
        
        if not text.strip():
            return jsonify({'error': 'Text must be provided'}), 400
            
        if len(text.strip()) < 10:
            return jsonify({'error': 'Please provide at least 10 characters'}), 400
        
        rephrased_text, changes = rephraser.rephrase_text(text, style, creativity)
        words_changed = len(changes)
        
        return jsonify({
            'rephrased_text': rephrased_text,
            'original_text': text,
            'original_length': len(text.split()),
            'rephrased_length': len(rephrased_text.split()),
            'words_changed': words_changed,
            'changes_made': changes,
            'style': style,
            'creativity': creativity
        })
    
    except Exception as e:
        return jsonify({'error': f'Rephrasing error: {str(e)}'}), 500

# Vercel handler
def handler(request):
    return app(request.environ, lambda *args: None)

if __name__ == '__main__':
    app.run(debug=True)
