# Frontend Integration Guide

## What Your Frontend Should Do

### Step-by-Step Process:

1. **Start Recording Audio**
   - Use browser's `MediaRecorder` API to capture audio from user's microphone
   - Record in a supported format (webm is recommended for browsers)
   - Store audio chunks as they're recorded

2. **Stop Recording**
   - Stop the MediaRecorder
   - Combine all audio chunks into a single Blob

3. **Send Audio to API**
   - Create a FormData object
   - Append the audio Blob with the key `audio`
   - Send POST request to `http://localhost:5001/api/speech/transcribe`

4. **Receive Transcript**
   - Parse the JSON response
   - If `success: true`, display the `transcript` field
   - If `success: false`, show the `error` message

---

## Example Flow (Pseudo-code)

```javascript
// 1. Start recording
const startRecording = async () => {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const mediaRecorder = new MediaRecorder(stream);
  const audioChunks = [];
  
  mediaRecorder.ondataavailable = (event) => {
    audioChunks.push(event.data);
  };
  
  mediaRecorder.start();
  return { mediaRecorder, audioChunks };
};

// 2. Stop recording and get audio blob
const stopRecording = (mediaRecorder, audioChunks) => {
  return new Promise((resolve) => {
    mediaRecorder.onstop = () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
      resolve(audioBlob);
    };
    mediaRecorder.stop();
  });
};

// 3. Send to API and get transcript
const transcribeAudio = async (audioBlob) => {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.webm');
  
  const response = await fetch('http://localhost:5001/api/speech/transcribe', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  return result;
};

// 4. Complete workflow
const recordAndTranscribe = async () => {
  // Start recording
  const { mediaRecorder, audioChunks } = await startRecording();
  
  // Wait for user to speak (e.g., show recording UI)
  // ...
  
  // Stop recording
  const audioBlob = await stopRecording(mediaRecorder, audioChunks);
  
  // Transcribe
  const result = await transcribeAudio(audioBlob);
  
  if (result.success) {
    console.log('Transcript:', result.transcript);
    // Display transcript to user
  } else {
    console.error('Error:', result.error);
    // Show error message to user
  }
};
```

---

## API Request Format

**Endpoint:** `POST http://localhost:5001/api/speech/transcribe`

**Headers:**
- Content-Type: `multipart/form-data` (automatically set by browser)

**Body:**
- FormData with field `audio` containing the audio file/blob

---

## Important Notes

1. **Audio Format**: Browser's MediaRecorder typically outputs `webm` format, which is supported
2. **File Size**: Keep recordings under 25MB
3. **CORS**: Already configured to allow requests from any origin (for development)
4. **Error Handling**: Always check the `success` field in the response
5. **Loading State**: Show a loading indicator while waiting for transcription (can take a few seconds)

---

## UI/UX Recommendations

1. **Recording Indicator**: Show visual feedback when recording (red dot, animation, etc.)
2. **Permission Request**: Handle microphone permission gracefully
3. **Audio Preview**: Optionally let users listen to their recording before transcription
4. **Loading State**: Show "Transcribing..." message during API call
5. **Error Messages**: Display user-friendly error messages
6. **Retry Option**: Allow users to record again if something goes wrong
