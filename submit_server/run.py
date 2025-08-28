#!/usr/bin/env python3
"""
Submit Server - Flask application for collecting user questions with video frames
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
SUBMISSIONS_FILE = '/root/hcmc/submit_server/submissions.json'
PORT = 5001

def load_submissions():
    """Load existing submissions from JSON file"""
    if os.path.exists(SUBMISSIONS_FILE):
        try:
            with open(SUBMISSIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading submissions: {e}")
            return {}
    return {}

def save_submissions(submissions):
    """Save submissions to JSON file"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(SUBMISSIONS_FILE), exist_ok=True)
        
        with open(SUBMISSIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(submissions, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"Error saving submissions: {e}")
        return False

@app.route('/submit', methods=['POST'])
def submit_question():
    """Submit a question with frame information"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['question', 'video_path', 'timestamp', 'frame_idx']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        question = data['question'].strip()
        if not question:
            return jsonify({'error': 'Question cannot be empty'}), 400
        
        # Load existing submissions
        submissions = load_submissions()
        
        # Create frame entry
        frame_entry = {
            'video_path': data['video_path'],
            'timestamp': float(data['timestamp']),
            'frame_idx': int(data['frame_idx']),
            'submitted_at': datetime.now().isoformat()
        }
        
        # Add to submissions
        if question not in submissions:
            submissions[question] = []
        
        submissions[question].append(frame_entry)
        
        # Save submissions
        if save_submissions(submissions):
            return jsonify({
                'success': True,
                'message': 'Question submitted successfully',
                'total_frames': len(submissions[question])
            })
        else:
            return jsonify({'error': 'Failed to save submission'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/submissions', methods=['GET'])
def get_submissions():
    """Get all submissions"""
    try:
        submissions = load_submissions()
        return jsonify(submissions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/submissions/<question>', methods=['GET'])
def get_question_submissions(question):
    """Get submissions for a specific question"""
    try:
        submissions = load_submissions()
        question_submissions = submissions.get(question, [])
        return jsonify({
            'question': question,
            'frames': question_submissions,
            'total_frames': len(question_submissions)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/questions', methods=['GET'])
def get_questions():
    """Get list of all questions"""
    try:
        submissions = load_submissions()
        questions = list(submissions.keys())
        return jsonify({
            'questions': questions,
            'total_questions': len(questions)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get submission statistics"""
    try:
        submissions = load_submissions()
        total_questions = len(submissions)
        total_frames = sum(len(frames) for frames in submissions.values())
        
        return jsonify({
            'total_questions': total_questions,
            'total_frames': total_frames,
            'submissions_file': SUBMISSIONS_FILE
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print(f"Starting Submit Server on port {PORT}")
    print(f"Submissions will be saved to: {SUBMISSIONS_FILE}")
    app.run(host='0.0.0.0', port=PORT, debug=True)