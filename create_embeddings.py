import os
import pickle
import cv2
import pandas as pd
import insightface

# Load InsightFace model
app = insightface.app.FaceAnalysis(name="buffalo_l")
app.prepare(ctx_id=1, det_size=(640, 640))

database_folder = "criminal_database"

# Read criminal information
criminal_info = pd.read_csv("criminal_database_3000.csv")
embeddings = []

for _, row in criminal_info.iterrows():

    image_name = row["image"]

    image_path = os.path.join(database_folder, image_name)

    image = cv2.imread(image_path)

    if image is None:
        print(f"Cannot read {image_name}")
        continue

    faces = app.get(image)

    if len(faces) == 0:
        print(f"No face found in {image_name}")
        continue

    embedding = faces[0].embedding

    embeddings.append({

        "image": image_name,

        "name": row["name"],

        "age": row["age"],

        "crime": row["crime"],

        "last_seen": row["last_seen"],

        "embedding": embedding

    })

print(f"Processed {len(embeddings)} faces")

with open("criminal_embeddings.pkl", "wb") as f:
    pickle.dump(embeddings, f)

print("criminal_embeddings.pkl created successfully!")