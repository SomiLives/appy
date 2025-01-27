let mediaRecorder;
let audioChunks = [];

document.getElementById('startBtn').addEventListener('click', async () => {
    try {
        let stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = event => audioChunks.push(event.data);

        mediaRecorder.onstop = () => {
            let audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            document.getElementById('audioPlayback').src = URL.createObjectURL(audioBlob);
            document.getElementById('uploadBtn').disabled = false;
        };

        mediaRecorder.start();
        document.getElementById('stopBtn').disabled = false;
        document.getElementById('startBtn').disabled = true;
    } catch (error) {
        alert('Error accessing microphone: ' + error);
    }
});

document.getElementById('stopBtn').addEventListener('click', () => {
    mediaRecorder.stop();
    document.getElementById('stopBtn').disabled = true;
    document.getElementById('startBtn').disabled = false;
});

document.getElementById('uploadBtn').addEventListener('click', async () => {
    let audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
    let formData = new FormData();
    formData.append('audio', audioBlob, 'lecture.wav');

    try {
        let response = await fetch('/upload-audio', { method: 'POST', body: formData });
        let data = await response.json();
        alert(data.message || data.error);
        audioChunks = [];
        document.getElementById('uploadBtn').disabled = true;
    } catch (error) {
        alert('Upload error: ' + error);
    }
});

document.getElementById('queryBtn').addEventListener('click', async () => {
    let question = document.getElementById('question').value.trim();
    if (!question) {
        alert('Please enter a question');
        return;
    }

    let response = await fetch('/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
    });

    let data = await response.json();
    document.getElementById('answer').innerText = data.answer ? "Answer: " + data.answer : "Error: " + data.error;
});

