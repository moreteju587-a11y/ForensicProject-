import cv2
import pickle
import numpy as np
import insightface

# Load InsightFace model
app = insightface.app.FaceAnalysis(name="buffalo_l")
app.prepare(ctx_id=-1)

# Load criminal embeddings
with open("criminal_embeddings.pkl", "rb") as f:
    criminal_db = pickle.load(f)


def find_top5_matches(image_path):

    image = cv2.imread(image_path)

    if image is None:
        return []

    faces = app.get(image)

    if len(faces) == 0:
        return []

    query_embedding = faces[0].embedding

    results = []

    for person in criminal_db:

        similarity = np.dot(query_embedding, person["embedding"]) / (
            np.linalg.norm(query_embedding)
            * np.linalg.norm(person["embedding"])
        )

        results.append({

            "image": person["image"],

            "name": person["name"],

            "age": person["age"],

            "crime": person["crime"],

            "last_seen": person["last_seen"],

            "similarity": round(float(similarity * 100), 2)

        })

    results = sorted(
        results,
        key=lambda x: x["similarity"],
        reverse=True
    )

    return results[:5]