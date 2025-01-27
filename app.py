from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
import mysql.connector
from mysql.connector import Error
from config import MYSQL_CONFIG
from models.whisper_processor import transcribe_audio
import openai
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()  # Ensure this is called

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Get OpenAI API Key from environment variable
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key not found. Please check your .env file.")

# Check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Connect to MySQL database
def get_db_connection():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG, charset="utf8mb4")
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
    return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    file = request.files['audio']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            file.save(filepath)
            print(f"File {filename} saved successfully at {filepath}")

            # Transcribe audio
            transcript = transcribe_audio(filepath)
            if not transcript:
                return jsonify({'error': 'Audio transcription failed'}), 500

            # Save to database
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO lectures (filename, transcript) VALUES (%s, %s)", (filename, transcript))
                conn.commit()
                cursor.close()
                conn.close()
                return jsonify({'message': 'Audio uploaded and transcribed successfully', 'transcript': transcript})
            else:
                return jsonify({'error': 'Database connection failed'}), 500
        except Exception as e:
            return jsonify({'error': f'File upload failed: {e}'}), 500
    else:
        return jsonify({'error': 'Invalid file format'}), 400


@app.route('/query', methods=['POST'])
def query():
    data = request.get_json()
    question = data.get('question')

    if not question:
        return jsonify({'error': 'No question provided'}), 400

    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT transcript FROM lectures")
            lectures = " ".join([row[0] for row in cursor.fetchall()])
            cursor.close()
            conn.close()

            if not lectures:
                return jsonify({'error': 'No lectures found in the database'}), 404
        else:
            return jsonify({'error': 'Database connection failed'}), 500

        # Use OpenAI API to process the query
        prompt = f"Based on the following lecture content, answer the question concisely:\n\n{lectures}\n\nQuestion: {question}"

        openai.api_key = OPENAI_API_KEY  # Ensure API key is set here
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI assistant specialized in summarizing and analyzing lecture transcripts."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )

        answer = response['choices'][0]['message']['content'].strip()

        if not answer:
            return jsonify({'error': 'OpenAI returned an empty response'}), 500

        return jsonify({'answer': answer})

    except Exception as e:
        return jsonify({'error': f'An error occurred: {e}'}), 500


if __name__ == '__main__':
    app.run(debug=True)

