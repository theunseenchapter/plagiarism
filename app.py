from flask import Flask, render_template, request, jsonify
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
import string
from collections import Counter
import difflib
import requests
from urllib.parse import quote
import time
import random

app = Flask(__name__)

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

class PlagiarismDetector:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 3))
        # Common phrases that might indicate plagiarism
        self.common_academic_phrases = [
            "in conclusion", "furthermore", "however", "moreover", "therefore",
            "according to", "as a result", "in addition", "on the other hand",
            "for example", "in other words", "it is important to note",
            "studies have shown", "research indicates", "it can be concluded",
            "first of all", "second of all", "last but not least", "to sum up",
            "in summary", "as mentioned above", "as stated previously"
        ]
        self.suspicious_patterns = [
            r'\b(?:copy|copied|paste|pasted|copypaste)\b',
            r'\b(?:wikipedia|wiki)\b',
            r'\b(?:source|sources)\s*:',
            r'(?:retrieved|accessed)\s+(?:from|on)',
            r'\b(?:doi|isbn|url|http|https|www)\b',
            r'©|\bcopyright\b|\ball rights reserved\b',
            r'\b(?:reference|references|bibliography)\b',
            r'\[\d+\]|\(\d{4}\)',  # Citations like [1] or (2020)
            r'\bet al\b|\betal\b',
            r'\bpp\?\s*\d+',  # Page numbers
            r'\bvol\.\s*\d+|\bvolume\s*\d+',
        ]
    
    def preprocess_text(self, text):
        """Clean and preprocess the text"""
        text = text.lower()
        text = text.translate(str.maketrans('', '', string.punctuation))
        text = ' '.join(text.split())
        return text
    
    def analyze_text_statistics(self, text):
        """Analyze basic text statistics"""
        sentences = sent_tokenize(text)
        words = word_tokenize(text)
        words_clean = [word.lower() for word in words if word.isalpha()]
        
        return {
            'total_words': len(words_clean),
            'total_sentences': len(sentences),
            'unique_words': len(set(words_clean)),
            'avg_words_per_sentence': round(len(words_clean) / len(sentences), 1) if sentences else 0
        }
    
    def detect_suspicious_patterns(self, text):
        """Detect patterns that might indicate copied content"""
        import re
        suspicious_found = []
        
        for pattern in self.suspicious_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                suspicious_found.append(match.group())
        
        return suspicious_found
    
    def analyze_sentence_structure(self, text):
        """Analyze sentence structure for potential copying indicators"""
        sentences = sent_tokenize(text)
        issues = []
        
        # Check for very long sentences (possible copy-paste)
        long_sentences = [s for s in sentences if len(s.split()) > 40]
        if long_sentences:
            issues.append(f"Found {len(long_sentences)} unusually long sentences that may indicate copying")
        
        # Check for very short sentences
        short_sentences = [s for s in sentences if len(s.split()) < 3]
        if len(short_sentences) > len(sentences) * 0.3:
            issues.append("High proportion of very short sentences detected")
        
        return issues
    
    def detect_common_phrases(self, text):
        """Detect overuse of common academic phrases"""
        text_lower = text.lower()
        found_phrases = []
        
        for phrase in self.common_academic_phrases:
            if phrase in text_lower:
                count = text_lower.count(phrase)
                if count > 1:
                    found_phrases.append(f"{phrase} (used {count} times)")
                else:
                    found_phrases.append(phrase)
        
        return found_phrases[:10]  # Return top 10
    
    def detect_wikipedia_like_content(self, text):
        """Detect content that resembles Wikipedia or encyclopedia entries"""
        wikipedia_indicators = [
            r'\bis a\b.*\bthat\b',  # "X is a Y that..."
            r'\bwas born\b.*\bin\b',
            r'\bis known for\b',
            r'\bis located in\b',
            r'\bis the capital of\b',
            r'\baccording to.*sources?\b',
            r'\bas of \d{4}\b',  # "as of 2020"
            r'\bcitation needed\b',
            r'\b\d{4}\b.*\b\d{4}\b',  # Multiple years like "1805... 1806"
            r'\bBattle of\b',  # Historical battles
            r'\bWar of\b',  # Historical wars
            r'\bin \d{4}\b',  # "in 1805", "in 1806"
            r'\bdefeated\b.*\bat\b',  # "defeated X at Y"
            r'\bled to\b.*\bof\b',  # "led to the X of Y"
            r'\bis considered\b.*\bin history\b',
            r'\bhis legacy\b',
            r'\bare still studied\b',
            r'\bembodied in\b',
            r'\bforcing\b.*\bto\b',  # "forcing X to Y"
            r'\bexiled\b.*\bto\b',  # "exiled to X"
            r'\bdied of\b.*\bin \d{4}\b',  # "died of X in YEAR"
        ]
        
        matches = 0
        matched_patterns = []
        for pattern in wikipedia_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                matches += 1
                # Extract the actual match for debugging
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    matched_patterns.append(match.group()[:30])  # First 30 chars
        
        return matches
    
    def detect_historical_content(self, text):
        """Detect historical/biographical content patterns"""
        historical_patterns = [
            r'\b\d{4}s?\b',  # Years like 1805, 1800s
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            r'\b(?:Emperor|King|Queen|Prince|Princess|Duke|General|Admiral)\b',
            r'\b(?:Empire|Kingdom|Republic|Coalition|Peninsula|Treaty)\b',
            r'\b(?:invaded|conquered|defeated|victory|battle|war|peace)\b',
            r'\b(?:throne|crown|reign|rule|power|abdicate)\b',
            r'\b(?:army|military|naval|forces|troops|soldiers)\b',
        ]
        
        matches = 0
        for pattern in historical_patterns:
            matches += len(re.findall(pattern, text, re.IGNORECASE))
        
        return matches
    
    def calculate_plagiarism_score(self, text):
        """Calculate an overall plagiarism risk score"""
        score = 0
        
        # Base score from text analysis
        stats = self.analyze_text_statistics(text)
        
        # Very high unique word ratio might indicate academic writing (lower risk)
        unique_ratio = stats['unique_words'] / stats['total_words'] if stats['total_words'] > 0 else 0
        if unique_ratio < 0.3:
            score += 25
        elif unique_ratio < 0.5:
            score += 15
        elif unique_ratio < 0.7:
            score += 5
        
        # Suspicious patterns (heavily weighted)
        suspicious = self.detect_suspicious_patterns(text)
        score += len(suspicious) * 20
        
        # Sentence structure issues
        structure_issues = self.analyze_sentence_structure(text)
        score += len(structure_issues) * 15
        
        # Common phrases overuse
        common_phrases = self.detect_common_phrases(text)
        if len(common_phrases) > 8:
            score += 25
        elif len(common_phrases) > 5:
            score += 15
        elif len(common_phrases) > 3:
            score += 10
        
        # Check for repetitive patterns
        words = word_tokenize(text.lower())
        word_freq = Counter(words)
        most_common = word_freq.most_common(5)
        
        # If top words appear too frequently, it might indicate copying
        if most_common and most_common[0][1] > len(words) * 0.1:
            score += 15
        
        # Very short text might be suspicious
        if len(words) < 20:
            score += 10
        
        # Check for inconsistent writing style (simple heuristic)
        sentences = sent_tokenize(text)
        if len(sentences) > 1:
            sentence_lengths = [len(sent.split()) for sent in sentences]
            avg_length = sum(sentence_lengths) / len(sentence_lengths)
            variance = sum((x - avg_length) ** 2 for x in sentence_lengths) / len(sentence_lengths)
            
            # High variance in sentence length might indicate copying
            if variance > 100:
                score += 10
        
        # Check for Wikipedia-like content
        wiki_score = self.detect_wikipedia_like_content(text)
        score += wiki_score * 8
        
        # Check for historical/biographical content (often copied from references)
        historical_score = self.detect_historical_content(text)
        if historical_score > 15:  # Many historical terms/dates
            score += 25
        elif historical_score > 10:
            score += 15
        elif historical_score > 5:
            score += 10
        
        # Check for very formal/encyclopedic writing style
        formal_indicators = len(re.findall(r'\b(?:however|furthermore|moreover|nevertheless|consequently|subsequently|thereby|wherein|whereby)\b', text, re.IGNORECASE))
        if formal_indicators > 3:
            score += 15
        elif formal_indicators > 1:
            score += 8
        
        # Cap at 100
        return min(score, 100)
    
    def detect_plagiarism(self, text):
        """Main single-text plagiarism detection function"""
        if not text.strip():
            return {"error": "Text must be provided"}
        
        # Analyze text statistics
        text_analysis = self.analyze_text_statistics(text)
        
        # Calculate plagiarism score
        plagiarism_score = self.calculate_plagiarism_score(text)
        
        # Detect issues
        suspicious_patterns = self.detect_suspicious_patterns(text)
        structure_issues = self.analyze_sentence_structure(text)
        common_phrases = self.detect_common_phrases(text)
        wiki_indicators = self.detect_wikipedia_like_content(text)
        historical_indicators = self.detect_historical_content(text)
        
        # Combine all issues
        all_issues = []
        if suspicious_patterns:
            pattern_list = list(set(suspicious_patterns))[:3]  # Remove duplicates, take first 3
            all_issues.append(f"Suspicious patterns detected: {', '.join(pattern_list)}")
        
        all_issues.extend(structure_issues)
        
        if len(common_phrases) > 3:
            all_issues.append(f"Overuse of common academic phrases detected ({len(common_phrases)} phrases)")
            
        if wiki_indicators > 3:
            all_issues.append(f"Content resembles encyclopedia/Wikipedia style ({wiki_indicators} indicators)")
        elif wiki_indicators > 1:
            all_issues.append(f"Some encyclopedia-style patterns detected ({wiki_indicators} indicators)")
            
        if historical_indicators > 15:
            all_issues.append(f"High concentration of historical/factual content ({historical_indicators} indicators)")
        elif historical_indicators > 10:
            all_issues.append(f"Significant historical/factual content detected ({historical_indicators} indicators)")
        elif historical_indicators > 5:
            all_issues.append(f"Historical/biographical content patterns found ({historical_indicators} indicators)")
        
        # Add more specific feedback
        stats = text_analysis
        unique_ratio = stats['unique_words'] / stats['total_words'] if stats['total_words'] > 0 else 0
        
        if unique_ratio < 0.3:
            all_issues.append("Very low vocabulary diversity - possible copied content")
        elif unique_ratio < 0.5:
            all_issues.append("Moderate vocabulary diversity - review for originality")
            
        # Check sentence length variance
        sentences = sent_tokenize(text)
        if len(sentences) > 1:
            sentence_lengths = [len(sent.split()) for sent in sentences]
            avg_length = sum(sentence_lengths) / len(sentence_lengths)
            variance = sum((x - avg_length) ** 2 for x in sentence_lengths) / len(sentence_lengths)
            
            if variance > 100:
                all_issues.append("Inconsistent sentence structure detected")
                
        # Check for overly factual/formal tone
        formal_indicators = len(re.findall(r'\b(?:however|furthermore|moreover|nevertheless|consequently|subsequently|thereby|wherein|whereby)\b', text, re.IGNORECASE))
        if formal_indicators > 3:
            all_issues.append("Highly formal/academic writing style detected")
        
        # Determine risk level - made more sensitive
        if plagiarism_score >= 60:
            plagiarism_level = "High"
            risk_color = "danger"
        elif plagiarism_score >= 35:
            plagiarism_level = "Medium"
            risk_color = "warning"
        elif plagiarism_score >= 15:
            plagiarism_level = "Low"
            risk_color = "info"
        else:
            plagiarism_level = "Very Low"
            risk_color = "success"
        
        return {
            'plagiarism_score': round(plagiarism_score, 1),
            'plagiarism_level': plagiarism_level,
            'risk_color': risk_color,
            'text_analysis': text_analysis,
            'suspicious_patterns': len(suspicious_patterns),
            'issues': all_issues,
            'common_phrases': common_phrases
        }

class TextRephraser:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.synonyms = {
            # Common words and their synonyms
            'important': ['significant', 'crucial', 'vital', 'essential', 'critical'],
            'big': ['large', 'huge', 'enormous', 'massive', 'substantial'],
            'small': ['tiny', 'little', 'miniature', 'compact', 'minor'],
            'good': ['excellent', 'outstanding', 'superior', 'remarkable', 'exceptional'],
            'bad': ['poor', 'inferior', 'inadequate', 'deficient', 'unsatisfactory'],
            'show': ['demonstrate', 'illustrate', 'reveal', 'display', 'exhibit'],
            'help': ['assist', 'support', 'aid', 'facilitate', 'enable'],
            'make': ['create', 'produce', 'generate', 'construct', 'develop'],
            'think': ['believe', 'consider', 'suppose', 'assume', 'conclude'],
            'many': ['numerous', 'several', 'various', 'multiple', 'countless'],
            'different': ['various', 'diverse', 'distinct', 'alternative', 'separate'],
            'use': ['utilize', 'employ', 'apply', 'implement', 'adopt'],
            'people': ['individuals', 'persons', 'citizens', 'population', 'society'],
            'way': ['method', 'approach', 'technique', 'manner', 'strategy'],
            'new': ['novel', 'recent', 'modern', 'contemporary', 'fresh'],
            'old': ['ancient', 'traditional', 'historical', 'vintage', 'established'],
            'first': ['initial', 'primary', 'earliest', 'foremost', 'beginning'],
            'last': ['final', 'ultimate', 'concluding', 'ending', 'terminal'],
            'also': ['additionally', 'furthermore', 'moreover', 'likewise', 'similarly'],
            'however': ['nevertheless', 'nonetheless', 'yet', 'although', 'whereas'],
            'because': ['since', 'due to', 'owing to', 'as a result of', 'given that'],
            'very': ['extremely', 'highly', 'considerably', 'significantly', 'remarkably'],
            'study': ['research', 'investigation', 'analysis', 'examination', 'inquiry'],
            'result': ['outcome', 'consequence', 'finding', 'conclusion', 'effect'],
            'problem': ['issue', 'challenge', 'difficulty', 'concern', 'obstacle'],
            'solution': ['resolution', 'answer', 'remedy', 'approach', 'fix'],
            'increase': ['enhance', 'boost', 'elevate', 'amplify', 'expand'],
            'decrease': ['reduce', 'diminish', 'lower', 'minimize', 'decline'],
            # Added more common words
            'said': ['stated', 'declared', 'mentioned', 'expressed', 'indicated'],
            'went': ['traveled', 'moved', 'proceeded', 'journeyed', 'advanced'],
            'came': ['arrived', 'appeared', 'emerged', 'approached', 'reached'],
            'see': ['observe', 'notice', 'witness', 'perceive', 'view'],
            'get': ['obtain', 'acquire', 'receive', 'gain', 'secure'],
            'give': ['provide', 'offer', 'supply', 'deliver', 'present'],
            'know': ['understand', 'realize', 'recognize', 'comprehend', 'grasp'],
            'take': ['seize', 'grab', 'capture', 'obtain', 'acquire'],
            'find': ['discover', 'locate', 'identify', 'uncover', 'detect'],
            'work': ['function', 'operate', 'perform', 'labor', 'effort'],
            'time': ['period', 'duration', 'moment', 'era', 'epoch'],
            'year': ['period', 'span', 'duration', 'cycle', 'season'],
            'day': ['period', 'time', 'date', 'occasion', 'moment'],
            'life': ['existence', 'being', 'living', 'vitality', 'experience'],
            'world': ['globe', 'earth', 'planet', 'universe', 'society'],
            'place': ['location', 'position', 'spot', 'site', 'area'],
            'home': ['residence', 'dwelling', 'house', 'abode', 'habitat'],
            'school': ['institution', 'academy', 'college', 'university', 'establishment'],
            'book': ['volume', 'text', 'publication', 'manuscript', 'work'],
            'car': ['vehicle', 'automobile', 'auto', 'transport', 'conveyance'],
            'family': ['relatives', 'household', 'clan', 'kin', 'lineage'],
            'friend': ['companion', 'associate', 'ally', 'colleague', 'partner'],
            'water': ['liquid', 'fluid', 'moisture', 'aqua', 'H2O'],
            'food': ['nourishment', 'sustenance', 'nutrition', 'provisions', 'cuisine'],
            'money': ['currency', 'funds', 'cash', 'capital', 'finance'],
            'love': ['affection', 'devotion', 'adoration', 'fondness', 'care'],
            'hate': ['despise', 'loathe', 'detest', 'abhor', 'dislike'],
            'like': ['enjoy', 'appreciate', 'favor', 'prefer', 'admire'],
            'want': ['desire', 'wish', 'crave', 'seek', 'require'],
            'need': ['require', 'demand', 'necessitate', 'lack', 'want'],
            'hope': ['wish', 'desire', 'expect', 'anticipate', 'trust'],
            'fear': ['dread', 'worry', 'anxiety', 'concern', 'apprehension'],
            'happy': ['joyful', 'cheerful', 'content', 'pleased', 'delighted'],
            'sad': ['sorrowful', 'melancholy', 'depressed', 'unhappy', 'mournful'],
            'angry': ['furious', 'irate', 'enraged', 'livid', 'incensed'],
            'surprised': ['astonished', 'amazed', 'shocked', 'startled', 'stunned'],
            'beautiful': ['gorgeous', 'stunning', 'attractive', 'lovely', 'elegant'],
            'ugly': ['hideous', 'unsightly', 'repulsive', 'unattractive', 'grotesque'],
            'strong': ['powerful', 'robust', 'sturdy', 'mighty', 'forceful'],
            'weak': ['feeble', 'frail', 'fragile', 'delicate', 'vulnerable'],
            'fast': ['quick', 'rapid', 'swift', 'speedy', 'hasty'],
            'slow': ['sluggish', 'gradual', 'leisurely', 'delayed', 'unhurried'],
            'high': ['tall', 'elevated', 'lofty', 'towering', 'soaring'],
            'low': ['short', 'reduced', 'minimal', 'diminished', 'inferior'],
            'long': ['lengthy', 'extended', 'prolonged', 'extensive', 'enduring'],
            'short': ['brief', 'concise', 'compact', 'abbreviated', 'limited'],
            'easy': ['simple', 'effortless', 'straightforward', 'uncomplicated', 'basic'],
            'hard': ['difficult', 'challenging', 'tough', 'demanding', 'complex'],
            'right': ['correct', 'accurate', 'proper', 'appropriate', 'suitable'],
            'wrong': ['incorrect', 'mistaken', 'erroneous', 'false', 'improper'],
            'true': ['accurate', 'correct', 'factual', 'genuine', 'authentic'],
            # Added more common words that appear in typical text
            'example': ['instance', 'illustration', 'sample', 'case', 'specimen'],
            'simple': ['basic', 'elementary', 'straightforward', 'uncomplicated', 'plain'],
            'text': ['content', 'material', 'writing', 'document', 'passage'],
            'changed': ['altered', 'modified', 'transformed', 'adjusted', 'revised'],
            'married': ['wed', 'united', 'joined', 'coupled', 'bonded'],
            'second': ['subsequent', 'following', 'next', 'additional', 'another'],
            'husband': ['spouse', 'partner', 'mate', 'companion', 'consort'],
            'young': ['youthful', 'juvenile', 'adolescent', 'immature', 'tender'],
            'moved': ['relocated', 'transferred', 'shifted', 'migrated', 'traveled'],
            'village': ['town', 'community', 'settlement', 'hamlet', 'locality'],
            'raise': ['rear', 'bring up', 'nurture', 'educate', 'cultivate'],
            'son': ['child', 'offspring', 'heir', 'descendant', 'progeny'],
            'daughter': ['child', 'offspring', 'girl', 'descendant', 'progeny'],
            'years': ['periods', 'decades', 'ages', 'eras', 'spans'],
            'death': ['demise', 'passing', 'end', 'expiration', 'departure'],
            'mother': ['parent', 'matriarch', 'maternal figure', 'mom', 'caregiver'],
            'father': ['parent', 'patriarch', 'paternal figure', 'dad', 'sire'],
            'examined': ['analyzed', 'studied', 'investigated', 'reviewed', 'inspected'],
            'state': ['condition', 'situation', 'status', 'circumstances', 'position'],
            'soul': ['spirit', 'essence', 'being', 'consciousness', 'psyche'],
            'compiled': ['assembled', 'collected', 'gathered', 'organized', 'prepared'],
            'catalog': ['list', 'inventory', 'register', 'index', 'collection'],
            'sins': ['wrongdoings', 'transgressions', 'offenses', 'misdeeds', 'violations'],
            'remembered': ['recalled', 'recollected', 'reminisced', 'thought of', 'brought to mind'],
            'threatening': ['menacing', 'intimidating', 'warning', 'endangering', 'frightening'],
            'house': ['home', 'residence', 'dwelling', 'abode', 'building'],
            'acute': ['severe', 'intense', 'sharp', 'extreme', 'critical'],
            'sense': ['feeling', 'perception', 'awareness', 'understanding', 'consciousness'],
            'insecurity': ['uncertainty', 'anxiety', 'doubt', 'vulnerability', 'instability'],
            'rendered': ['made', 'caused', 'created', 'produced', 'generated'],
            'obsessively': ['compulsively', 'fixatedly', 'intensely', 'persistently', 'excessively'],
            'anxious': ['worried', 'concerned', 'nervous', 'troubled', 'uneasy'],
            'published': ['released', 'issued', 'printed', 'distributed', 'circulated'],
            'irrational': ['unreasonable', 'illogical', 'senseless', 'absurd', 'groundless'],
            'violent': ['aggressive', 'brutal', 'fierce', 'destructive', 'harsh'],
            'defended': ['protected', 'safeguarded', 'supported', 'upheld', 'maintained'],
            'accompanied': ['went with', 'followed', 'escorted', 'joined', 'attended'],
            'throughout': ['during', 'across', 'over', 'through', 'all through'],
            'traced': ['tracked', 'followed', 'pursued', 'identified', 'detected'],
            'early': ['initial', 'beginning', 'preliminary', 'first', 'starting']
        }
        
        self.sentence_starters = {
            'academic': [
                'Research indicates that',
                'Studies have shown that',
                'Evidence suggests that',
                'Analysis reveals that',
                'Findings demonstrate that',
                'Investigation shows that',
                'Data indicates that',
                'Examination reveals that'
            ],
            'formal': [
                'It can be observed that',
                'It is evident that',
                'One can conclude that',
                'It appears that',
                'It seems that',
                'It is clear that',
                'It is apparent that',
                'One might argue that'
            ],
            'casual': [
                'It turns out that',
                'Basically,',
                'In simple terms,',
                'What this means is',
                'The thing is,',
                'Here\'s what happens:',
                'Simply put,',
                'In other words,'
            ],
            'simple': [
                'This shows that',
                'We can see that',
                'This means that',
                'We found that',
                'This tells us that',
                'We learned that',
                'This proves that',
                'We discovered that'
            ]
        }
    
    def rephrase_text(self, text, style='academic', creativity='medium'):
        """Rephrase text to reduce plagiarism while maintaining meaning"""
        sentences = sent_tokenize(text)
        rephrased_sentences = []
        changes_made = []
        
        for sentence in sentences:
            rephrased, sentence_changes = self.rephrase_sentence(sentence, style, creativity)
            rephrased_sentences.append(rephrased)
            changes_made.extend(sentence_changes)
        
        return ' '.join(rephrased_sentences), changes_made
    
    def rephrase_sentence(self, sentence, style, creativity):
        """Rephrase a single sentence and track changes"""
        words = word_tokenize(sentence)
        rephrased_words = []
        changes = []
        
        # Determine replacement probability based on creativity level
        replacement_prob = {
            'low': 0.4,
            'medium': 0.6,
            'high': 0.8
        }.get(creativity, 0.6)
        
        for i, word in enumerate(words):
            word_lower = word.lower()
            # Check if word is alphabetic and not a stop word
            if word.isalpha() and word_lower not in self.stop_words:
                if random.random() < replacement_prob and word_lower in self.synonyms:
                    # Replace with synonym
                    synonym = random.choice(self.synonyms[word_lower])
                    # Preserve original capitalization
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
            else:
                rephrased_words.append(word)
        
        # Reconstruct sentence
        rephrased = ' '.join(rephrased_words)
        
        # Sometimes add a different sentence starter based on style
        if random.random() < 0.3 and style in self.sentence_starters:
            starter = random.choice(self.sentence_starters[style])
            rephrased = f"{starter} {rephrased.lower()}"
            changes.append({
                'original': 'sentence_start',
                'replacement': starter,
                'position': -1
            })
        
        return rephrased, changes
    
    def improve_structure(self, text, style):
        """Improve sentence structure and flow"""
        sentences = sent_tokenize(text)
        
        if len(sentences) <= 1:
            return text
        
        # Add transitional phrases between sentences
        transitions = {
            'academic': [
                'Furthermore,', 'Moreover,', 'Additionally,', 'In addition,',
                'Consequently,', 'Therefore,', 'Thus,', 'Hence,',
                'However,', 'Nevertheless,', 'On the other hand,'
            ],
            'formal': [
                'Subsequently,', 'Furthermore,', 'In addition,', 'Moreover,',
                'Consequently,', 'Therefore,', 'However,', 'Nevertheless,'
            ],
            'casual': [
                'Also,', 'Plus,', 'And,', 'But,', 'So,', 'Then,', 'Now,'
            ],
            'simple': [
                'Also,', 'Then,', 'Next,', 'But,', 'So,', 'And,'
            ]
        }
        
        improved_sentences = [sentences[0]]  # Keep first sentence as is
        
        for i in range(1, len(sentences)):
            if random.random() < 0.4:  # 40% chance to add transition
                transition = random.choice(transitions.get(style, transitions['formal']))
                improved_sentences.append(f"{transition} {sentences[i]}")
            else:
                improved_sentences.append(sentences[i])
        
        return ' '.join(improved_sentences)

# Initialize the detector
detector = PlagiarismDetector()

# Initialize rephraser
rephraser = TextRephraser()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text.strip():
            return jsonify({'error': 'Text must be provided and cannot be empty'}), 400
        
        if len(text.strip()) < 50:
            return jsonify({'error': 'Please provide at least 50 characters for meaningful analysis'}), 400
        
        result = detector.detect_plagiarism(text)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': f'An error occurred during analysis: {str(e)}'}), 500

@app.route('/rephrase', methods=['POST'])
def rephrase():
    try:
        data = request.json
        text = data.get('text', '')
        style = data.get('style', 'academic')
        creativity = data.get('creativity', 'medium')
        
        if not text.strip():
            return jsonify({'error': 'Text must be provided and cannot be empty'}), 400
        
        if len(text.strip()) < 10:
            return jsonify({'error': 'Please provide at least 10 characters for rephrasing'}), 400
        
        # Rephrase the text
        rephrased_text, changes_made = rephraser.rephrase_text(text, style, creativity)
        
        # Improve structure
        improved_text = rephraser.improve_structure(rephrased_text, style)
        
        # Count the number of words changed
        words_changed = len([c for c in changes_made if c['original'] != 'sentence_start'])
        
        # Debug: print changes for verification
        print(f"Debug: {words_changed} words changed")
        for change in changes_made[:5]:  # Print first 5 changes
            print(f"  {change['original']} -> {change['replacement']}")
        
        return jsonify({
            'rephrased_text': improved_text,
            'original_text': text,
            'original_length': len(text.split()),
            'rephrased_length': len(improved_text.split()),
            'words_changed': words_changed,
            'changes_made': changes_made,
            'style': style,
            'creativity': creativity
        })
    
    except Exception as e:
        return jsonify({'error': f'An error occurred during rephrasing: {str(e)}'}), 500

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    import os
    # Use PORT environment variable for deployment platforms
    port = int(os.environ.get('PORT', 5000))
    # Use host 0.0.0.0 for external access
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
