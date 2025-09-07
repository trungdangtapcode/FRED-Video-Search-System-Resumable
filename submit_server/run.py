#!/usr/bin/env python3
"""
Submit Server - Flask application for collecting user questions with video frames
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
import cv2
import tempfile
import numpy as np
from datetime import datetime
from io import BytesIO

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
SUBMISSIONS_FILE = '/data/root/hcmc/submit_server/submissions.json'
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
        from config import ROOT_DIR
        
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
        
        # Add ROOT_DIR back to the relative video path for storage
        relative_video_path = data['video_path'].lstrip('/')
        full_video_path = os.path.join(ROOT_DIR, relative_video_path)
        
        # Create frame entry with full path
        frame_entry = {
            'video_path': full_video_path,
            'timestamp': float(data['timestamp']),
            'frame_idx': int(data['frame_idx']),
            'submitted_at': datetime.now().isoformat()
        }
        
        # Add optional answer field if provided
        if 'answer' in data and data['answer'] and data['answer'].strip():
            frame_entry['answer'] = data['answer'].strip()
        
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

@app.route('/delete', methods=['POST'])
def delete_frame():
    """Delete a specific frame from submissions"""
    try:
        from config import ROOT_DIR
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['question', 'video_path', 'timestamp', 'frame_idx']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        question = data['question'].strip()
        relative_video_path = data['video_path'].lstrip('/')
        full_video_path = os.path.join(ROOT_DIR, relative_video_path)
        timestamp = float(data['timestamp'])
        frame_idx = int(data['frame_idx'])
        
        # Load existing submissions
        submissions = load_submissions()
        
        if question not in submissions:
            return jsonify({'error': 'Question not found'}), 404
        
        # Find and remove the matching frame (compare with full path)
        original_count = len(submissions[question])
        submissions[question] = [
            frame for frame in submissions[question]
            if not (frame['video_path'] == full_video_path and 
                   frame['timestamp'] == timestamp and 
                   frame['frame_idx'] == frame_idx)
        ]
        
        # Remove question entirely if no frames left
        if len(submissions[question]) == 0:
            del submissions[question]
        
        # Check if anything was actually deleted
        deleted_count = original_count - len(submissions.get(question, []))
        if deleted_count == 0:
            return jsonify({'error': 'Frame not found'}), 404
        
        # Save submissions
        if save_submissions(submissions):
            return jsonify({
                'success': True,
                'message': 'Frame deleted successfully',
                'deleted_count': deleted_count,
                'remaining_frames': len(submissions.get(question, []))
            })
        else:
            return jsonify({'error': 'Failed to save changes'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reorder', methods=['POST'])
def reorder_frames():
    """Reorder frames within a question"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'question' not in data or 'frames' not in data:
            return jsonify({'error': 'Missing required fields: question, frames'}), 400
        
        question = data['question'].strip()
        new_frames = data['frames']
        
        if not question:
            return jsonify({'error': 'Question cannot be empty'}), 400
        
        if not isinstance(new_frames, list):
            return jsonify({'error': 'Frames must be a list'}), 400
        
        # Load existing submissions
        submissions = load_submissions()
        
        if question not in submissions:
            return jsonify({'error': 'Question not found'}), 404
        
        # Update the frames order for the question
        submissions[question] = new_frames
        
        # Save submissions
        if save_submissions(submissions):
            return jsonify({
                'success': True,
                'message': 'Frames reordered successfully'
            })
        else:
            return jsonify({'error': 'Failed to save changes'}), 500
            
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
    
from flask import request, jsonify, send_file
from io import BytesIO
import os
import imageio.v3 as iio
import numpy as np
@app.route('/extract_frame', methods=['GET'])
def extract_frame():
    """Extract frame from video at specific timestamp"""
    try:
        from config import ROOT_DIR
        
        relative_video_path = request.args.get('video_path')
        timestamp = request.args.get('timestamp')
        
        if not relative_video_path or not timestamp:
            return jsonify({'error': 'Missing video_path or timestamp parameter'}), 400
        
        try:
            timestamp = float(timestamp)
        except ValueError:
            return jsonify({'error': 'Invalid timestamp format'}), 400
        
        # Add ROOT_DIR back to the relative path
        full_video_path = os.path.join(ROOT_DIR, relative_video_path.lstrip('/'))
        
        # Check if video file exists
        if not os.path.exists(full_video_path):
            return jsonify({'error': 'Video file not found'}), 404
        
        # Open video file
        cap = cv2.VideoCapture(full_video_path)
        if not cap.isOpened():
            return jsonify({'error': 'Could not open video file'}), 500
        
        # Set video position to the specified timestamp
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)  # Convert to milliseconds
        
        # Read the frame
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return jsonify({'error': 'Could not read frame at specified timestamp'}), 500
        
        # Convert frame to JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        # Create BytesIO object
        img_io = BytesIO(buffer.tobytes())
        img_io.seek(0)
        
        return send_file(
            img_io,
            mimetype='image/jpeg',
            as_attachment=False,
            download_name=f'frame_{timestamp}.jpg'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print(f"Starting Submit Server on port {PORT}")
    print(f"Submissions will be saved to: {SUBMISSIONS_FILE}")
    app.run(host='0.0.0.0', port=PORT, debug=True)