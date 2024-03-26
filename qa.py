
import os
from moondream import Moondream, detect_device, LATEST_REVISION
from transformers import AutoTokenizer
from PIL import Image
import shutil

device, dtype = detect_device()

model_id = "vikhyatk/moondream2"
tokenizer = AutoTokenizer.from_pretrained(model_id, revision=LATEST_REVISION)
moondream = Moondream.from_pretrained(
    model_id,
    revision=LATEST_REVISION,
    torch_dtype=dtype,
).to(device=device)
moondream.eval()

# Function to check if a file path contains "_"
def contains_underscore(file_path):
    return '_' in file_path

# Function to check if a file path contains "nsfw"
def contains_nsfw(file_path):
    return 'nsfw' in file_path.lower()

# Directory containing images
directory = "../output"

# Iterate through all subdirectories and files
for root, dirs, files in os.walk(directory):
    for file in files:
        if file.endswith(".png"):
            file_path = os.path.join(root, file)
            if contains_underscore(file_path) and not contains_nsfw(file_path):
                image = Image.open(file_path)
                prompts = [
                    "Answer with an integer only: how many people are in the picture?",
                    "Answer yes or no: is everyone wearing a top?",
                    "Answer only yes or no: could this be from the medieval era?"]

                answers = moondream.batch_answer(
                    images=[image, image, image, image],
                    prompts=prompts,
                    tokenizer=tokenizer,
                )

                # Extract answers
                people_count = int(answers[0])
                nudity_score = answers[1].lower()
                medieval_era = answers[2].lower()
                unusual_limbs = answers[3].lower()

                print(f"File: {file_path}")
                print(f"Number of people: {people_count}")
                print(f"Is everyone wearing a top {nudity_score}")
                print(f"Medieval looking: {medieval_era}")
                #print(f"Unusual number of legs/arms: {unusual_limbs}")

                if nudity_score == "no":
                    if "female" in root:
                        print("Moving the image and JSON file to NSFW directory.")
                        # Calculate NSFW directory based on the parent directory of the image
                        parent_dir = os.path.dirname(file_path)
                        parent_name = os.path.basename(parent_dir)
                        nsfw_directory = os.path.join(os.path.dirname(parent_dir), f"{parent_name}_NSFW")
                        if not os.path.exists(nsfw_directory):
                            os.makedirs(nsfw_directory)
                        # Move image file
                        shutil.move(file_path, nsfw_directory)
                        # Move corresponding JSON file
                        json_file = os.path.splitext(file)[0] + ".json"
                        json_file_path = os.path.join(root, json_file)
                        shutil.move(json_file_path, nsfw_directory)
                    else:
                        print("Deleting the image because male nudity.")
                        os.remove(file_path)
                        # Delete corresponding JSON file
                        json_file = os.path.splitext(file)[0] + ".json"
                        json_file_path = os.path.join(root, json_file)
                        if os.path.exists(json_file_path):
                            os.remove(json_file_path)
                elif people_count != 1:
                    print("Deleting the image because the number of people is not 1.")
                    os.remove(file_path)
                    # Delete corresponding JSON file
                    json_file = os.path.splitext(file)[0] + ".json"
                    json_file_path = os.path.join(root, json_file)
                    if os.path.exists(json_file_path):
                        os.remove(json_file_path)
                elif medieval_era == "no":
                    print("Deleting the image because it does not look medieval.")
                    os.remove(file_path)
                    # Delete corresponding JSON file
                    json_file = os.path.splitext(file)[0] + ".json"
                    json_file_path = os.path.join(root, json_file)
                    if os.path.exists(json_file_path):
                        os.remove(json_file_path)
                else:
                    print("Image is safe.")

                print()
