import whisper

def load_model(model_size="small"):
    model = whisper.load_model(model_size)
    return model

def transcribe_audio(file_path, model):
    result = model.transcribe(file_path)
    return result["text"]
