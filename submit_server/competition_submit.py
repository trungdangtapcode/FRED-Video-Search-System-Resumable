"""
Competition submission module for submitting answers to the competition server
"""

import json
import os
import requests
from typing import Dict, Any, Optional

# Competition server configuration
COMPETITION_SERVER = 'https://eventretrieval.oj.io.vn'
SESSION_ID = 'ojMnP01scNwS2XgGFxGiBCD6PCqpXhyl'  # Set your session ID here
EVALUATION_ID = 'a5970b9e-9779-466b-916b-b2f7471103a6'  # Set your evaluation ID here
# EVALUATION_ID = '03a5b5b4-761e-4222-8478-c499900fb28f'
EVALUATION_ID = '6a5a2861-c922-437e-9ce4-c24fe2fa97f9'
EVALUATION_ID = '06236d7d-368e-44ac-a388-c955cb374a7d'


def format_kis_submission(video_id: str, timestamp_ms: int) -> Dict[str, Any]:
    """Format KIS submission body"""
    return {
        'answerSets': [{
            'answers': [{
                'mediaItemName': video_id,
                'start': timestamp_ms,
                'end': timestamp_ms
            }]
        }]
    }


def format_qa_submission(video_id: str, timestamp_ms: int, answer: str) -> Dict[str, Any]:
    """Format QA submission body"""
    if not answer:
        raise ValueError('Answer is required for QA questions')
    
    return {
        'answerSets': [{
            'answers': [{
                'text': f'QA-{answer}-{video_id}-{timestamp_ms}'
            }]
        }]
    }


def format_trake_submission(video_id: str, frame_indices: list) -> Dict[str, Any]:
    """Format TRAKE submission body"""
    # Join frame indices with commas
    frame_indices.sort()
    frame_list = ','.join(str(idx) for idx in frame_indices)
    return {
        'answerSets': [{
            'answers': [{
                'text': f'TR-{video_id}-{frame_list}'
            }]
        }]
    }


def submit_to_competition(
    question_type: str,
    video_path: str,
    timestamp: float,
    frame_idx: int,
    answer: Optional[str] = None,
    all_frames: Optional[list] = None  # For TRAKE: list of all frames in question
) -> Dict[str, Any]:
    """
    Submit an answer to the competition server
    
    Args:
        question_type: One of 'KIS', 'QA', or 'TRAKE'
        video_path: Path to the video file
        timestamp: Timestamp in seconds
        frame_idx: Frame index
        answer: Answer text (required for QA questions)
        all_frames: List of all frames (required for TRAKE questions)
    
    Returns:
        Dict containing success status, evaluation_id, and competition response
    
    Raises:
        ValueError: If question_type is invalid or required fields are missing
        Exception: If submission fails
    """
    question_type = question_type.upper()
    
    if question_type not in ['KIS', 'QA', 'TRAKE']:
        raise ValueError('Invalid question_type. Must be KIS, QA, or TRAKE')
    
    if not EVALUATION_ID:
        raise ValueError('EVALUATION_ID not configured')
    
    if not SESSION_ID:
        raise ValueError('SESSION_ID not configured')
    
    # Extract video ID from video path
    video_id = os.path.basename(video_path).replace('.mp4', '')
    
    # Convert timestamp to milliseconds
    timestamp_ms = int(timestamp * 1000)
    if timestamp_ms==0:
        raise ValueError('co thang nao submit 0ms khong?')
        return
    
    # Format submission based on question type
    if question_type == 'KIS':
        submission_body = format_kis_submission(video_id, timestamp_ms)
    elif question_type == 'QA':
        submission_body = format_qa_submission(video_id, timestamp_ms, answer)
    else:  # TRAKE
        # For TRAKE, we need all frames in the question
        if not all_frames:
            raise ValueError('all_frames is required for TRAKE questions')
        
        # Extract frame indices from all frames
        frame_indices = [frame['frame_idx'] for frame in all_frames]
        submission_body = format_trake_submission(video_id, frame_indices)
    

    print("BODY: ", submission_body)
    # Submit to competition server
    submit_url = f'{COMPETITION_SERVER}/api/v2/submit/{EVALUATION_ID}'
    print('url:', submit_url)
    submit_response = requests.post(
        submit_url,
        params={'session': SESSION_ID},
        json=submission_body,
        headers={'Content-Type': 'application/json'}
    )
    
    if not submit_response.ok:
        raise Exception(
            f'Failed to submit to competition server: {submit_response.text} '
            f'(Status: {submit_response.status_code})'
        )
    
    # Parse response
    response_data = submit_response.json() if submit_response.text else {}
    
    # Check submission result
    # status: True means submission was accepted (not rejected by filters)
    # submission: 'CORRECT' or 'WRONG' indicates if the answer is correct
    submission_status = response_data.get('status', False)
    submission_result = response_data.get('submission', '')
    description = response_data.get('description', '')
    
    print(f'Competition submission response: {response_data}')
    print(f"Status: {'Accepted' if submission_status else 'Rejected'}, Result: {submission_result}, Description: {description}")
    
    # Determine if this should be shown as success or error
    # Only show success if status is True AND submission is CORRECT
    is_success = submission_status and submission_result == 'CORRECT'
    
    # Return response with actual status from competition server
    return {
        'success': is_success,
        'message': description,
        'submission_result': submission_result,  # CORRECT, WRONG, or empty
        'evaluation_id': EVALUATION_ID,
        'competition_response': response_data
    }
