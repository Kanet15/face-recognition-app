import pickle
import os

ENCODING_FILE = 'known_faces.pkl'

if os.path.exists(ENCODING_FILE) and os.path.getsize(ENCODING_FILE) > 0:
    with open(ENCODING_FILE, 'rb') as f:
        data = pickle.load(f)
    print("Contents of known_faces.pkl:")
    for entry in data:
        print(f"  Name: {entry.get('name')}, ID: {entry.get('id')}, Encoding length: {len(entry.get('encoding')) if entry.get('encoding') else 0}")
else:
    print("known_faces.pkl not found or is empty.")