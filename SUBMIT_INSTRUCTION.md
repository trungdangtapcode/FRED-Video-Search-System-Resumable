# API Instructions

## Step 1: Get Evaluation ID

**GET** request to `/api/v2/client/evaluation/list`

**Parameters:**
```json
{
  "session": "<sessionID>"
}
```

**Response:**
```json
[
  {
    "id": "<evaluationID>",
    "status": "ACTIVE"
  }
]
```

## Step 2: Submit Answer

**POST** request to `/api/v2/submit/{evaluationID}?session=<sessionID>`

### Body Format for KIS:
```json
{
  "answerSets": [{
    "answers": [{
      "mediaItemName": "<VIDEO_ID>",
      "start": "<TIME(ms)>",
      "end": "<TIME(ms)>"
    }]
  }]
}
```

### Body Format for QA:
```json
{
  "answerSets": [{
    "answers": [{
      "text": "QA-<ANSWER>-<VIDEO_ID>-<TIME(ms)>"
    }]
  }]
}
```

### Body Format for TRAKE:
```json
{
  "answerSets": [{
    "answers": [{
      "text": "TR-<VIDEO_ID>-<FRAME_ID1>,<FRAME_ID2>,..."
    }]
  }]
}
```

The server url to submit is `https://eventretrieval.oj.io.vn/`