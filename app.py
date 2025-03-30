import streamlit as st
import ollama
import speech_recognition as sr
import pyttsx3
import tempfile
import os
import time
import uuid
from audio_recorder_streamlit import audio_recorder

# Initialize text-to-speech engine
def text_to_speech(text):
    engine = pyttsx3.init()
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
        temp_filename = tmp_file.name
    engine.save_to_file(text, temp_filename)
    engine.runAndWait()
    return temp_filename

# Function to convert speech to text
def speech_to_text(audio_bytes):
    recognizer = sr.Recognizer()
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
        tmp_file.write(audio_bytes)
        tmp_file_path = tmp_file.name
    
    try:
        with sr.AudioFile(tmp_file_path) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data)
                return text
            except:
                return "Sorry, I couldn't understand that."
    finally:
        # Use try-except to handle file deletion errors
        try:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
        except Exception as e:
            st.error(f"Error removing temp file: {e}")

# Function to get response from Llama 3.1
def get_llama_response(prompt, history):
    context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
    response = ollama.chat(
        model="llama3.1:8b", 
        messages=[{"role": "system", "content": f"Previous conversation:\n{context}"},
                 {"role": "user", "content": prompt}]
    )
    return response['message']['content']

# Function to autoplay audio
def autoplay_audio(file_path):
    try:
        with open(file_path, "rb") as f:
            audio_bytes = f.read()
        st.audio(audio_bytes, format="audio/mp3", start_time=0)
    finally:
        # Use try-except to handle file deletion errors
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            st.error(f"Error removing audio file: {e}")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi! How may I assist you today?", "id": str(uuid.uuid4())}]

# App title
st.title("Voice Chatbot with Llama 3.1 🤖")

# Display chat messages
for idx, message in enumerate(st.session_state.messages):
    with st.container():
        if message["role"] == "user":
            st.text_area("User", message["content"], height=100, key=f"user_{idx}_{message.get('id', '')}")
        else:
            st.text_area("Assistant", message["content"], height=100, key=f"assistant_{idx}_{message.get('id', '')}")

# Text input option
prompt = st.text_input("Type your message here...")
if st.button("Send") and prompt:
    # Add user message to chat history
    user_msg_id = str(uuid.uuid4())
    st.session_state.messages.append({"role": "user", "content": prompt, "id": user_msg_id})
    
    # Get response from Llama
    with st.spinner("Thinking..."):
        response = get_llama_response(prompt, st.session_state.messages)
    
    # Add assistant response to chat history
    assistant_msg_id = str(uuid.uuid4())
    st.session_state.messages.append({"role": "assistant", "content": response, "id": assistant_msg_id})
    
    # Generate audio response
    audio_file = text_to_speech(response)
    autoplay_audio(audio_file)
    
    # Rerun to update UI
    st.experimental_rerun()

# Voice input option
st.write("Or speak your message:")
audio_bytes = audio_recorder()
if audio_bytes:
    # Convert speech to text
    with st.spinner("Processing audio..."):
        text = speech_to_text(audio_bytes)
    
    # Add user message to chat history
    user_msg_id = str(uuid.uuid4())
    st.session_state.messages.append({"role": "user", "content": text, "id": user_msg_id})
    
    # Get response from Llama
    with st.spinner("Thinking..."):
        response = get_llama_response(text, st.session_state.messages)
    
    # Add assistant response to chat history
    assistant_msg_id = str(uuid.uuid4())
    st.session_state.messages.append({"role": "assistant", "content": response, "id": assistant_msg_id})
    
    # Generate audio response
    audio_file = text_to_speech(response)
    autoplay_audio(audio_file)
    
    # Rerun to update UI
    st.experimental_rerun()