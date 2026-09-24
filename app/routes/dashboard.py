from flask import Blueprint, render_template, session, jsonify, current_app, request
from app.routes.auth import login_required
from app.services.dna_service import SAMPLE_SEQUENCES
from app.services.chatbot_service import _call_ollama
from datetime import datetime
import random
import logging

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

DNA_FACTS = [
    "Human DNA is about 99.9% identical from person to person.",
    "If uncoiled, the DNA in all your cells would stretch to Pluto and back.",
    "About 8% of human DNA is made of ancient viral fragments.",
    "We share about 60% of our DNA with bananas and fruit flies.",
    "DNA has a half-life of 521 years and degrades over time.",
    "A single gram of DNA can store roughly 215 petabytes of data.",
    "Identical twins have the exact same DNA code.",
    "There are over 3 billion base pairs in the human genome.",
    "Genes make up only about 1% to 2% of human DNA.",
    "The DNA double helix was discovered by Watson, Crick, and Franklin in 1953."
]

def get_time_greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Morning"
    elif 12 <= hour < 17:
        return "Afternoon"
    elif 17 <= hour < 22:
        return "Evening"
    else:
        return "Night"

@dashboard_bp.route('/')
@login_required
def index():
    greeting_time = get_time_greeting()
    # Provide a random fallback fact initially so the UI doesn't look empty
    random_fact = random.choice(DNA_FACTS)
    return render_template('dashboard/index.html', samples=SAMPLE_SEQUENCES, greeting_time=greeting_time, dna_fact=random_fact)

@dashboard_bp.route('/api/dna-fact')
@login_required
def get_dna_fact():
    lang = request.args.get('lang', 'en')
    
    # Very strictly bound prompt to avoid long paragraphs or medical advice
    prompt = (
        "Generate one short, interesting and scientifically accurate fact about DNA, genetics, chromosomes, "
        "genes, mutations, or bioinformatics. Return only the fact in 1-2 sentences. "
        "Do not provide medical advice. Do not add conversational filler like 'Here is a fact'."
    )
    
    try:
        model = current_app.config.get("OLLAMA_MODEL", "llama3.2")
        base_url = current_app.config.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        
        # Override the normal conversation history to just this prompt
        fact = _call_ollama(
            message=prompt,
            language=lang,
            conversation=[],
            model=model,
            base_url=base_url
        )
        
        if fact and len(fact) > 5:
            # Strip quotes if the model wrapped it in quotes
            fact = fact.strip('"\'')
            return jsonify({"fact": fact, "source": "ollama"})
            
    except Exception as e:
        logger.warning(f"Failed to fetch DNA fact from Ollama: {str(e)}")
        
    # Fallback if Ollama fails or times out
    return jsonify({"fact": random.choice(DNA_FACTS), "source": "fallback"})
