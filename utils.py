import face_recognition
import numpy as np
from models import Person



# --- Face Recognition Core Functions ---

def get_face_encoding(image_path):
    """
    Return the face encoding of the first detected face.
    """
    try:
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)
        if encodings:
            return encodings[0]  return encodings[0]  # First detected face
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
    return None

def serialize_encoding(encoding):
    """
    Convert a face encoding to a string.
    """
    return ','.join(map(str, encoding))

def deserialize_encoding(encoding_str):
    """
    Convert a stored encoding string back to a NumPy array.
    """
    return np.array(encoding_str.split(','), dtype=float)

def find_matches(face_encoding, top_n=5):
    def find_matches(face_encoding, top_n=5):
    """
    Compare a face encoding with all registered persons.
    Return the top matching results.
    """
    persons = Person.query.all()
    if not persons:
        return []

    # Load face encodings from the database
    known_encodings = [deserialize_encoding(p.face_encoding) for p in persons]
    
    # Calculate the distance between the uploaded face and registered faces.
    # Smaller distance indicates a better match.
    face_distances = face_recognition.face_distance(known_encodings, face_encoding)
    results = []
    for i, person in enumerate(persons):
        distance = face_distances[i]
       # Convert face distance to a similarity percentage.
        similarity = max(0, (1 - distance) * 100) 
        
        # Keep only matches above the similarity threshold.
        if similarity > 50:
            results.append({
                'person': person,
                'similarity': round(similarity, 2)
            })

    # Sort matches by highest similarity
    results.sort(key=lambda x: x['similarity'], reverse=True)

    return results[:top_n]

