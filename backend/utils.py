import face_recognition
import numpy as np
import pickle
import os
from typing import List, Tuple, Union, Dict

ENCODING_FILE = 'known_faces.pkl'

def get_face_encoding(image_path: str) -> np.ndarray:
    """
    Extract face encoding from an image file

    Args:
        image_path: Path to the image file

    Returns:
        numpy array of face encoding

    Raises:
        ValueError: If no face found, multiple faces found, or encoding fails
    """
    try:
        image = face_recognition.load_image_file(image_path)
        face_locations = face_recognition.face_locations(image)

        if not face_locations:
            raise ValueError("ไม่พบใบหน้าในภาพ")

        if len(face_locations) > 1:
            raise ValueError("มีใบหน้ามากกว่า 1 หน้าในภาพ กรุณาอัปโหลดภาพที่มีใบหน้าชัดเจน 1 หน้าเท่านั้น")

        face_encodings = face_recognition.face_encodings(image, face_locations)

        if not face_encodings:
            raise ValueError("ไม่สามารถสร้าง encoding จากภาพได้")

        # Ensure it's a numpy array
        return np.array(face_encodings[0])

    except Exception as e:
        if isinstance(e, ValueError):
            raise
        else:
            raise ValueError(f"เกิดข้อผิดพลาดในการประมวลผลภาพ: {str(e)}")

def load_known_faces() -> Tuple[List[np.ndarray], List[str], List[str]]:
    """
    Load known faces from pickle file

    Returns:
        Tuple of (encodings, names, ids)
    """
    if not os.path.exists(ENCODING_FILE) or os.path.getsize(ENCODING_FILE) == 0:
        return [], [], []

    try:
        with open(ENCODING_FILE, 'rb') as f:
            data = pickle.load(f)

        # Convert back to numpy arrays if they were stored as lists
        known_encodings = []
        known_names = []
        known_ids = []

        for item in data:
            # Handle both numpy arrays and lists
            encoding = item['encoding']
            if isinstance(encoding, list):
                encoding = np.array(encoding)

            known_encodings.append(encoding)
            known_names.append(item['name'])
            known_ids.append(item['id'])

        return known_encodings, known_names, known_ids

    except Exception as e:
        print(f"Error loading known faces: {e}")
        return [], [], []

def save_face_encoding_data(name: str, user_id: str, encoding: np.ndarray) -> None:
    """
    Save face encoding data to pickle file

    Args:
        name: Person's name
        user_id: Person's ID
        encoding: Face encoding as numpy array
    """
    data = []

    # Load existing data if file exists
    if os.path.exists(ENCODING_FILE) and os.path.getsize(ENCODING_FILE) > 0:
        try:
            with open(ENCODING_FILE, 'rb') as f:
                data = pickle.load(f)
        except Exception as e:
            print(f"Warning: Could not load existing data: {e}")
            data = []

    # Check if this person already exists (optional: could update instead)
    existing_ids = [item['id'] for item in data]
    if user_id in existing_ids:
        print(f"Warning: User ID {user_id} already exists. Adding duplicate entry.")

    # Add new entry
    new_entry = {
        "name": name,
        "id": user_id,
        "encoding": encoding.tolist()  # Convert to list for JSON serialization compatibility
    }

    data.append(new_entry)

    # Save updated data
    try:
        with open(ENCODING_FILE, 'wb') as f:
            pickle.dump(data, f)
        print(f"Successfully saved encoding for {name} (ID: {user_id})")
    except Exception as e:
        raise RuntimeError(f"Failed to save face encoding data: {e}")

def recognize_face(unknown_encoding: np.ndarray, tolerance: float = 0.6) -> Tuple[Union[str, None], Union[str, None], float]:
    """
    Recognize a face by comparing with known faces

    Args:
        unknown_encoding: Face encoding to match
        tolerance: Face matching tolerance (lower = stricter)

    Returns:
        Tuple of (name, id, confidence) or (None, None, 0.0) if no match
    """
    known_encodings, known_names, known_ids = load_known_faces()

    if not known_encodings:
        return None, None, 0.0

    # Calculate face distances
    face_distances = face_recognition.face_distance(known_encodings, unknown_encoding)

    # Find the best match
    best_match_index = np.argmin(face_distances)
    best_distance = face_distances[best_match_index]

    if best_distance <= tolerance:
        confidence = 1.0 - best_distance  # Convert distance to confidence
        return known_names[best_match_index], known_ids[best_match_index], confidence
    else:
        return None, None, 0.0

def get_all_known_faces() -> List[dict]:
    """
    Get all known faces data

    Returns:
        List of dictionaries with name, id, and encoding info
    """
    known_encodings, known_names, known_ids = load_known_faces()

    result = []
    for i in range(len(known_names)):
        result.append({
            "name": known_names[i],
            "id": known_ids[i],
            "has_encoding": True
        })

    return result

# ⬇️ เพิ่มตรงนี้สำหรับ real-time
def recognize_faces_in_image(image_array: np.ndarray) -> List[Dict[str, Union[List[int], str, float]]]:
    known_encodings, known_names, known_ids = load_known_faces()

    face_locations = face_recognition.face_locations(image_array)
    face_encodings = face_recognition.face_encodings(image_array, face_locations)

    results = []
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.6)
        face_distances = face_recognition.face_distance(known_encodings, face_encoding)
        best_match_index = np.argmin(face_distances) if len(face_distances) > 0 else None

        name = "Unknown"
        user_id = "Unknown"
        confidence = 0.0

        if best_match_index is not None and matches[best_match_index]:
            name = known_names[best_match_index]
            user_id = known_ids[best_match_index]
            confidence = 1 - face_distances[best_match_index]

        results.append({
            "box": [top, right, bottom, left],
            "name": name,
            "id": user_id,
            "confidence": float(confidence)
        })

    return results