#!/usr/bin/env python3
"""
Google Translate Server
Provides translation services for the video search application.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from googletrans import Translator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Initialize Google Translator
translator = Translator()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "translate-server"})

@app.route('/translate', methods=['POST'])
def translate_text():
    """
    Translate text from one language to another.
    
    Expected request body:
    {
        "text": "text to translate",
        "src": "vi",  # source language (optional, auto-detect if not provided)
        "dest": "en"  # destination language (default: en)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({"error": "Missing 'text' parameter"}), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({"error": "Empty text provided"}), 400
        
        src_lang = data.get('src', 'auto')  # Auto-detect source language
        dest_lang = data.get('dest', 'en')  # Default to English
        
        logger.info(f"Translating text: '{text[:50]}...' from {src_lang} to {dest_lang}")
        
        # Perform translation
        result = translator.translate(text, src=src_lang, dest=dest_lang)
        
        response = {
            "original_text": text,
            "translated_text": result.text,
            "src_language": result.src,
            "dest_language": dest_lang,
            "confidence": getattr(result, 'confidence', None)
        }
        
        logger.info(f"Translation successful: '{result.text[:50]}...'")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        return jsonify({"error": f"Translation failed: {str(e)}"}), 500

@app.route('/translate/vietnamese-to-english', methods=['POST'])
def translate_vietnamese_to_english():
    """
    Convenience endpoint to translate Vietnamese to English.
    
    Expected request body:
    {
        "text": "text in Vietnamese to translate"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({"error": "Missing 'text' parameter"}), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({"error": "Empty text provided"}), 400
        
        logger.info(f"Translating Vietnamese text: '{text[:50]}...' to English")
        
        # Translate from Vietnamese to English
        result = translator.translate(text, src='vi', dest='en')
        
        response = {
            "original_text": text,
            "translated_text": result.text,
            "src_language": "vi",
            "dest_language": "en"
        }
        
        logger.info(f"Translation successful: '{result.text[:50]}...'")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        return jsonify({"error": f"Translation failed: {str(e)}"}), 500

@app.route('/detect-language', methods=['POST'])
def detect_language():
    """
    Detect the language of the provided text.
    
    Expected request body:
    {
        "text": "text to detect language for"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({"error": "Missing 'text' parameter"}), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({"error": "Empty text provided"}), 400
        
        logger.info(f"Detecting language for: '{text[:50]}...'")
        
        # Detect language
        detection = translator.detect(text)
        
        response = {
            "text": text,
            "language": detection.lang,
            "confidence": detection.confidence
        }
        
        logger.info(f"Language detected: {detection.lang} (confidence: {detection.confidence})")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Language detection error: {str(e)}")
        return jsonify({"error": f"Language detection failed: {str(e)}"}), 500

if __name__ == '__main__':
    logger.info("Starting Google Translate Server on port 5002...")
    app.run(host='0.0.0.0', port=13023, debug=False)