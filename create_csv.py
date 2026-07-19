import os
import csv

folder = "criminal_database"

with open("criminal_database.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)

    # Header
    writer.writerow(["image", "name", "age", "crime", "last_seen"])

    # One row for every image
    for image in sorted(os.listdir(folder)):
        if image.endswith(".jpg"):
            writer.writerow([image, "", "", "", ""])

print("CSV created successfully.")