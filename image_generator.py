import torch
from diffusers import StableDiffusionPipeline
from diffusers import DPMSolverMultistepScheduler
import os
import uuid

device = "cuda" if torch.cuda.is_available() else "cpu"

model_id = "SG161222/Realistic_Vision_V6.0_B1_noVAE"

print("Loading Realistic Vision model...")

pipe = StableDiffusionPipeline.from_pretrained(
    model_id,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    safety_checker=None,
    feature_extractor=None
)

pipe = pipe.to(device)
pipe.scheduler = DPMSolverMultistepScheduler.from_config(
    pipe.scheduler.config
)

pipe.enable_attention_slicing()
pipe.enable_vae_slicing()

print("Model loaded!")

def generate_face(prompt):

    negative_prompt = (
        "blurry, low quality, worst quality, deformed face, "
        "bad anatomy, extra eyes, extra nose, extra mouth, "
        "cropped, watermark, text, cartoon, painting"
    )

    image = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        num_inference_steps=20,
        guidance_scale=8.5,
        width=512,
        height=768
    ).images[0]

    output_folder = os.path.join("static", "generated_faces")
    os.makedirs(output_folder, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.png"

    output_path = os.path.join(output_folder, filename)

    image.save(output_path)

    return output_path
    