from flask import Flask, request, jsonify
from flask_cors import CORS
import librosa
import numpy as np
import tempfile
import os

app = Flask(__name__)

# Configure CORS to allow all origins
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@app.route('/')
def home():
    return jsonify({
        'status': 'ok',
        'message': 'Beat Detector API is running',
        'endpoints': {
            '/detect-beats': 'POST - Upload audio file to detect beats'
        }
    })

@app.route('/detect-beats', methods=['POST'])
def detect_beats():
    try:
        # Get parameters
        sensitivity = float(request.form.get('sensitivity', 1.0))
        detect_extra = request.form.get('detect_extra', 'false').lower() == 'true'
        
        # Get audio file
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.filename)[1]) as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            # Load audio with librosa
            print(f"Loading audio: {temp_path}")
            y, sr = librosa.load(temp_path, sr=None)
            duration = len(y) / sr
            print(f"Audio loaded: {duration:.2f}s, {sr}Hz")
            
            # Detect beats using librosa (same as our Python script)
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units='time')
            bpm = float(tempo)
            
            print(f"BPM: {bpm}, Beats: {len(beats)}")
            
            # Calculate onset strength for energy classification
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            
            # Classify beats by energy
            classified_beats = classify_beats(beats, onset_env, sr, sensitivity)
            
            # Add extra beats if requested
            if detect_extra:
                extra_beats = detect_extra_beats(y, sr, classified_beats, onset_env, sensitivity)
                classified_beats.extend(extra_beats)
                classified_beats.sort(key=lambda x: x['time'])
            
            # Extrapolate at beginning and end
            classified_beats = extrapolate_beats(classified_beats, bpm, duration)
            
            print(f"Final beats: {len(classified_beats)}")
            
            # Return results
            return jsonify({
                'success': True,
                'bpm': round(bpm),
                'beats': classified_beats,
                'duration': duration,
                'sample_rate': sr
            })
            
        finally:
            # Clean up temp file
            os.unlink(temp_path)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def classify_beats(beat_times, onset_env, sr, sensitivity):
    """Classify beats by energy (same logic as Python script)"""
    beats = []
    hop_length = 512
    
    for i, time in enumerate(beat_times):
        # Get frame index
        frame_idx = int(time * sr / hop_length)
        
        # Get energy in window around beat
        window_size = 5
        energy = 0
        for j in range(-window_size, window_size + 1):
            idx = frame_idx + j
            if 0 <= idx < len(onset_env):
                energy += onset_env[idx]
        
        # Normalize energy
        energy = energy / (2 * window_size + 1)
        
        # Determine level based on energy and position in bar
        beat_in_bar = i % 4
        
        if beat_in_bar == 0 and energy > 0.75 * sensitivity:
            level = 1  # Red - downbeat
        elif beat_in_bar == 2 and energy > 0.5 * sensitivity:
            level = 2  # Orange
        elif energy > 0.6 * sensitivity:
            level = 3  # Yellow
        else:
            level = 4  # Blue
        
        beats.append({
            'time': float(time),
            'level': level,
            'strength': float(energy)
        })
    
    return beats


def detect_extra_beats(y, sr, existing_beats, onset_env, sensitivity):
    """Detect extra beats between main beats"""
    extra_beats = []
    hop_length = 512
    
    # Find peaks in onset envelope
    existing_times = [b['time'] for b in existing_beats]
    min_distance = 0.1  # 100ms minimum
    
    for i in range(1, len(onset_env) - 1):
        # Check if it's a peak
        if onset_env[i] > onset_env[i-1] and onset_env[i] > onset_env[i+1]:
            time = (i * hop_length) / sr
            
            # Check if too close to existing beat
            too_close = any(abs(time - t) < min_distance for t in existing_times)
            
            if not too_close and onset_env[i] > 0.3 * sensitivity:
                level = 1 if onset_env[i] > 0.8 * sensitivity else 2
                extra_beats.append({
                    'time': float(time),
                    'level': level,
                    'strength': float(onset_env[i])
                })
    
    return extra_beats


def extrapolate_beats(beats, bpm, duration):
    """Fill gaps at beginning and end with blue markers"""
    if not beats:
        return beats
    
    beat_interval = 60.0 / bpm
    min_gap = 1.0  # Fill gaps > 1 second
    result = []
    
    # Fill beginning
    first_time = beats[0]['time']
    if first_time > min_gap:
        t = first_time - beat_interval
        while t >= 0:
            result.append({'time': float(t), 'level': 4, 'strength': 0.0})
            t -= beat_interval
    
    result.sort(key=lambda x: x['time'])
    result.extend(beats)
    
    # Fill end
    last_time = beats[-1]['time']
    if duration - last_time > min_gap:
        t = last_time + beat_interval
        while t < duration:
            result.append({'time': float(t), 'level': 4, 'strength': 0.0})
            t += beat_interval
    
    return result


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
