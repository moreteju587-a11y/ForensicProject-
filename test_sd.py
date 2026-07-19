from image_generator import generate_face

prompt = """
Ultra realistic passport photo of an Indian male,
30 years old,
oval face,
brown eyes,
short black hair,
trimmed beard,
neutral expression,
white background,
highly detailed
"""

path = generate_face(prompt)

print(path)