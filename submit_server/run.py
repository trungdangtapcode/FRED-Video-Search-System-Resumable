#!/usr/bin/env python3
"""
Submit Server - Flask application for collecting user questions with video frames
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import csv
import json
import os
import subprocess
from datetime import datetime
from io import BytesIO
from pathlib import Path

from config import FPS_VIDEO_PATH, ROOT_DIR, STATEMENTS_FILE, SUBMISSIONS_FILE

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
PORT = int(os.getenv("SUBMIT_PORT", "13022"))

with open(FPS_VIDEO_PATH, 'r') as f:
    VIDEO_FPS_DATA = json.load(f)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


def resolve_video_path(video_path: str) -> Path:
    """Resolve a submitted path while preventing access outside data/."""
    data_root = Path(ROOT_DIR).resolve()
    candidate = Path(video_path)
    if not candidate.is_absolute() or not candidate.is_relative_to(data_root):
        candidate = data_root / str(video_path).lstrip("/")
    candidate = candidate.resolve()
    try:
        candidate.relative_to(data_root)
    except ValueError as exc:
        raise ValueError("Video path is outside the configured data directory") from exc
    return candidate

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

def load_question_descriptions():
    """Load question descriptions keyed by question ID from statement.csv."""
    descriptions = {}
    try:
        with open(STATEMENTS_FILE, 'r', encoding='utf-8-sig', newline='') as f:
            for row in csv.reader(f):
                if len(row) < 2:
                    continue
                question_id = row[0].strip()
                description = ','.join(row[1:]).strip()
                if question_id:
                    descriptions[question_id] = description
    except IOError as e:
        print(f"Error loading question descriptions: {e}")
    return descriptions

def save_submissions(submissions):
    """Save submissions to JSON file"""
    try:
        # Ensure directory exists (only if there's a directory in the path)
        dir_name = os.path.dirname(SUBMISSIONS_FILE)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        
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
        if data['frame_idx'] < 0:
            video_id = os.path.basename(data['video_path']).replace('.mp4', '')
            fps =  VIDEO_FPS_DATA.get(video_id, -1) 
            if fps != -1:
                data['frame_idx'] = int(fps * float(data['timestamp']))

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
        
        # Resolve the frontend's data-relative path for storage.
        full_video_path = str(resolve_video_path(data['video_path']))
        
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
            response_data = {
                'success': True,
                'message': 'Question submitted successfully',
                'total_frames': len(submissions[question])
            }
            
            # If submit_directly is True, also submit to competition
            if data.get('submit_directly', False):
                try:
                    from competition_submit import submit_to_competition as do_submit
                    
                    # Determine question type
                    lower_question = question.lower()
                    if 'trake' in lower_question:
                        question_type = 'TRAKE'
                        # Get all frames for TRAKE
                        all_frames = submissions[question]
                    elif frame_entry.get('answer'):
                        question_type = 'QA'
                        all_frames = None
                    else:
                        question_type = 'KIS'
                        all_frames = None
                    
                    # Submit to competition
                    competition_result = do_submit(
                        question_type=question_type,
                        video_path=full_video_path,
                        timestamp=float(data['timestamp']),
                        frame_idx=int(data['frame_idx']),
                        answer=frame_entry.get('answer'),
                        all_frames=all_frames
                    )
                    
                    response_data['competition_result'] = competition_result
                except Exception as comp_error:
                    print(f"Competition submission error: {comp_error}")
                    response_data['competition_result'] = {
                        'success': False,
                        'message': str(comp_error)
                    }
            
            return jsonify(response_data)
        else:
            return jsonify({'error': 'Failed to save submission'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/submit_to_competition', methods=['POST'])
def submit_to_competition():
    """Submit a question to the competition server"""
    try:
        from competition_submit import submit_to_competition as do_submit
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['question_type', 'video_path', 'timestamp', 'frame_idx']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Extract data
        question_type = data['question_type']
        video_path = data['video_path']
        timestamp = float(data['timestamp'])
        frame_idx = int(data['frame_idx'])
        answer = data.get('answer', '')
        all_frames = data.get('all_frames', None)  # For TRAKE questions
        
        # Submit to competition
        result = do_submit(
            question_type=question_type,
            video_path=video_path,
            timestamp=timestamp,
            frame_idx=frame_idx,
            answer=answer,
            all_frames=all_frames
        )
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
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

@app.route('/statements', methods=['GET'])
def get_question_descriptions():
    """Get question descriptions keyed by question ID."""
    try:
        return jsonify(load_question_descriptions())
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
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['question', 'video_path', 'timestamp', 'frame_idx']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        question = data['question'].strip()
        full_video_path = str(resolve_video_path(data['video_path']))
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

@app.route('/extract_frame', methods=['GET'])
def extract_frame():
    """Extract frame from video at specific timestamp"""
    try:
        relative_video_path = request.args.get('video_path')
        timestamp = request.args.get('timestamp')
        
        if not relative_video_path or not timestamp:
            return jsonify({'error': 'Missing video_path or timestamp parameter'}), 400
        
        try:
            timestamp = float(timestamp)
        except ValueError:
            return jsonify({'error': 'Invalid timestamp format'}), 400
        
        full_video_path = resolve_video_path(relative_video_path)
        
        # Check if video file exists
        if not full_video_path.is_file():
            return jsonify({'error': 'Video file not found'}), 404

        process = subprocess.run(
            [
                "ffmpeg", "-loglevel", "error", "-ss", str(timestamp),
                "-i", str(full_video_path), "-frames:v", "1",
                "-q:v", "3", "-f", "image2pipe", "-vcodec", "mjpeg", "pipe:1",
            ],
            check=False,
            capture_output=True,
            timeout=30,
        )
        if process.returncode != 0 or not process.stdout:
            message = process.stderr.decode("utf-8", errors="replace")[-500:]
            return jsonify({'error': f'Could not extract frame: {message}'}), 500

        img_io = BytesIO(process.stdout)
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
    app.run(
        host=os.getenv("SUBMIT_HOST", "127.0.0.1"),
        port=PORT,
        debug=False,
    )
