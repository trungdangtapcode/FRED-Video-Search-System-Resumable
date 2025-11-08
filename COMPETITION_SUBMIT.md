# Competition Submission Setup

## Configuration

Edit `submit_server/competition_submit.py` and set both:

```python
SESSION_ID = 'your-session-id-here'
EVALUATION_ID = 'your-evaluation-id-here'
```

## Usage

1. **Hold "P" key** on the Submissions page
2. **Click any frame** to submit to competition
3. System auto-detects question type (KIS/QA/TRAKE) from question text
4. Toast notification shows success/error

## Question Type Detection

Add markers to your questions:
- `-kis` or `(kis)` → KIS submission
- `-qa` or `(qa)` → QA submission  
- `-trake` or `(trake)` → TRAKE submission

Examples:
- "Find the red car (KIS)"
- "What color is the car? (QA)"
- "Track object through frames (TRAKE)"

## Keyboard Shortcuts

- **P** - Submit to competition
- **X** - Delete frame
- **C** - Reorder frames
