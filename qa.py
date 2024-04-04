import os
import time
from moondream import Moondream, detect_device, LATEST_REVISION
from transformers import AutoTokenizer
from PIL import Image
import shutil
import re
import os
import shutil
import torch

import json

def load_json(filename):
     with open(filename, 'r') as file:
        data = json.load(file)
        return data

def lookup_answer(question, json_data):
    if 'metadata' in json_data:
        for metadata in json_data['metadata']:
            if question in metadata:
                return metadata[question]
    return None

def add_metadata(prompts, answers, filename):
    # Read existing JSON file
    with open(filename, 'r') as file:
        data = json.load(file)
    
    # Create metadata dictionary
    metadata = {}
    for prompt, answer in zip(prompts, answers):
        metadata[prompt] = answer
    
    # Add metadata to existing data
    if 'metadata' not in data:
        data['metadata'] = []
    data['metadata'].append(metadata)
    
    # Write updated data back to JSON file
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)
    return data

def extract_height(string):
    print("extracting height from string " + string)
    # Define the regular expression pattern to match integers or floating-point numbers
    pattern = r"\d+(?:\.\d+)?"
    # Search for the pattern in the string
    match = re.search(pattern, string)
    if match:
        # Extract and return the matched number
        return float(match.group()) if '.' in match.group() else int(match.group())
    else:
        # If no match found, return None or handle as needed
        return None

def delete_empty_subdirectories(root_dir):
    # Walk through all directories and subdirectories in the root_dir
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
        # Check if the directory is empty
        if not any(filenames) and "_" in dirpath:
            # Delete the empty directory
            shutil.rmtree(dirpath)
            print(f"Deleted empty directory: {dirpath}")

# Specify the root directory
root_directory = "../output"

print("starting qa.py")


device, dtype = detect_device()
#begin debugging code

#device = "cuda"
#dtype = torch.float32 if device == "cpu" else torch.float16 # CPU doesn't support float16
print("device = " +str(device))
#end debugging code
model_id = "vikhyatk/moondream2"
tokenizer = AutoTokenizer.from_pretrained(model_id, revision=LATEST_REVISION)
moondream = Moondream.from_pretrained(
    model_id,
    revision=LATEST_REVISION,
    torch_dtype=dtype,
).to(device=device)
moondream.eval()

def move_these_files(source_png, output_dir, subdir_name):
    # Create the output directory if it does not exist
    if not os.path.exists(output_dir):
        print("move_these_files:  making directory " + output_dir )
        os.makedirs(output_dir)

    # Create the subdirectory under the output directory
    sub_dir_path = os.path.join(output_dir, subdir_name)
    if not os.path.exists(sub_dir_path):
        print("move_these_files:  making directory " + sub_dir_path )
        os.makedirs(sub_dir_path)

    # Move corresponding PNG files to the same directory
    #png_file_name = os.path.splitext(file_name)[0] + '.png'
    src_png = os.path.join("../output",sub_directory, source_png)
    dest_png = os.path.join(sub_dir_path, source_png)
    if os.path.exists(src_png):
        shutil.move(src_png, dest_png)
    else:
        print("source image does not exist!!!  " + src_png)
    json_filename= source_png.split(".")[0]+".json"
    src_json = os.path.splitext(src_png)[0] + '.json'    
    dest_json = os.path.join(output_dir, sub_dir_path,json_filename )
    if os.path.exists(src_json):
        shutil.move(src_json, dest_json)
    else:
        print("src_json does not exist!!! " + src_json)           


def move_files(input_dir, output_dir, subdir_name):
    # Create the output directory if it does not exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Create the subdirectory under the output directory
    sub_dir_path = os.path.join(output_dir, subdir_name)
    if not os.path.exists(sub_dir_path):
        os.makedirs(sub_dir_path)

    # Iterate through all files in the input directory
    for file_name in os.listdir(input_dir):
        if file_name.endswith('.json'):
            # Move JSON files to the subdirectory under the output directory
            src_json = os.path.join(input_dir, file_name)
            dest_json = os.path.join(sub_dir_path, file_name)
            shutil.move(src_json, dest_json)

            # Move corresponding PNG files to the same directory
            png_file_name = os.path.splitext(file_name)[0] + '.png'
            src_png = os.path.join(input_dir, png_file_name)
            dest_png = os.path.join(sub_dir_path, png_file_name)
            if os.path.exists(src_png):
                shutil.move(src_png, dest_png)


# Function to check if a file path contains "_"
def contains_underscore(file_path):
    return '_' in file_path

# Function to check if a file path contains "nsfw"
def contains_nsfw(file_path):
    return 'nsfw' in file_path.lower()

# Directory containing images
directory = "../output"

total_time = 0
total_images = 0

# Iterate through all subdirectories and files
for root, dirs, files in os.walk(directory):
    print("Processing directory:", root)
    for file in files:
        if file.endswith(".png"):
            file_path = os.path.join(root, file)
            if contains_underscore(file_path) and not contains_nsfw(file_path):
                start_time = time.time()
                print("Processing " + file)
                image = Image.open(file_path)
                desc = "Medieval " + os.path.basename(root).replace("_"," ")
                print(desc)
                questions={
                            "people_count":"Answer with an integer only: how many people are in the picture?",
                            "wearing_top":"Answer yes or no: is everyone wearing a top?",
                            "accuracy":"On a scale of 1-10, how much does this look like a single person who is a " + desc,
                            "heightinfeet": "Answer as an integer: what is the height of the person rounded to the nearest foot in feet?",
                            "beard":"Answer yes or no: does this person have a beard?"

                        }

                question_order=["people_count","wearing_top", "accuracy", "heightinfeet","beard"]
                src_json = os.path.splitext(file_path)[0] + '.json'
                json_data = load_json(src_json)
                for k in questions:
                    if lookup_answer(questions[k], json_data) is not None:
                        question_order.remove(k) 
                prompts = []
                for q in question_order:
                        prompts.append(questions[q])                                                       
                images=[] 
                while len(images) < len(prompts):
                    images.append(image)
                if len(prompts)>0:
                    answers = moondream.batch_answer(
                        images=images,
                        prompts=prompts,
                        tokenizer=tokenizer,
                    )
                end_time = time.time()
                processing_time = end_time - start_time
                total_time += processing_time
                total_images += 1

                print(f"Processing time for {file}: {processing_time} seconds")
                print(f"Average processing time per image: {total_time / total_images} seconds")
                json_data=add_metadata(prompts, answers,  src_json)

                people_count = int(lookup_answer(questions["people_count"], json_data))
                wearing_top = lookup_answer(questions["wearing_top"],json_data).lower()
                accuracy = int(lookup_answer(questions["accuracy"],json_data))
                heightinfeet = extract_height(lookup_answer(questions["heightinfeet"],json_data))
                beard = lookup_answer(questions["beard"],json_data).lower()

                # people_count = int(answers[question_order.index("people_count")])
                # wearing_top = answers[question_order.index("wearing_top")].lower()
                # accuracy = int(answers[question_order.index("accuracy")].lower())
                # heightinfeet = extract_height(answers[question_order.index("heightinfeet")])
                # beard = answers[question_order.index("beard")].lower()

                
                print(f"File: {file_path}")
                print(f"Number of people: {people_count}")
                print(f"Is everyone wearing a top {wearing_top}")
                #print(f"Medieval looking: {medieval_era}")
                #print(f"gender: {gender}")
                print(f"accuracy: {accuracy}")
                #print(f"gender: {gender}")
                #print(f"only one person: {onlyoneperson}")
                print(f"beard: {beard}")
                    # print(f"height: {height}")
                
                #print(f"Unusual number of legs/arms: {unusual_limbs}")

                if wearing_top == "no":
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
                elif accuracy <8:
                    print("Deleting due to low accuracy")
                    os.remove(file_path)
                    # Delete corresponding JSON file
                    json_file = os.path.splitext(file)[0] + ".json"
                    json_file_path = os.path.join(root, json_file)
                    if os.path.exists(json_file_path):
                        os.remove(json_file_path)
                elif "dwarf" in desc and beard and beard == "no" :
                    print("Deleting due to no dwarfs without beards")
                    os.remove(file_path)
                    # Delete corresponding JSON file
                    json_file = os.path.splitext(file)[0] + ".json"
                    json_file_path = os.path.join(root, json_file)
                    if os.path.exists(json_file_path):
                        os.remove(json_file_path)
                elif heightinfeet is not None and heightinfeet <3 or heightinfeet >7:
                    print("Deleting due to height <3 or >7")
                    os.remove(file_path)
                    # Delete corresponding JSON file
                    json_file = os.path.splitext(file)[0] + ".json"
                    json_file_path = os.path.join(root, json_file)
                    if os.path.exists(json_file_path):
                        os.remove(json_file_path)
                # elif onlyoneperson == "no":
                #     print("Deleting the image because there is more than one person")
                #     os.remove(file_path)
                #     # Delete corresponding JSON file
                #     json_file = os.path.splitext(file)[0] + ".json"
                #     json_file_path = os.path.join(root, json_file)
                #     if os.path.exists(json_file_path):
                #         os.remove(json_file_path)
                elif people_count != 1:
                    print("Deleting the image because the number of people is not 1.")
                    os.remove(file_path)
                    # Delete corresponding JSON file
                    json_file = os.path.splitext(file)[0] + ".json"
                    json_file_path = os.path.join(root, json_file)
                    if os.path.exists(json_file_path):
                        os.remove(json_file_path)
                # elif medieval_era == "no":
                #     print("Deleting the image because it does not like the right gender")
                #     os.remove(file_path)
                #     # Delete corresponding JSON file
                #     json_file = os.path.splitext(file)[0] + ".json"
                #     json_file_path = os.path.join(root, json_file)
                #     if os.path.exists(json_file_path):
                #         os.remove(json_file_path)
                # elif gender == "male" and "female" in file_path or gender == "female" and "female" not in file_path:
                #     print("Deleting the image because it does not look like the right gender.")
                #     os.remove(file_path)
                #     # Delete corresponding JSON file
                #     json_file = os.path.splitext(file)[0] + ".json"
                #     json_file_path = os.path.join(root, json_file)
                #     if os.path.exists(json_file_path):
                #         os.remove(json_file_path)
                
                else:
                    print("Image is safe.")
                    src_json = os.path.splitext(file_path)[0] + '.json'  
                    add_metadata(prompts, answers,  src_json)
                    sub_directory = os.path.basename(root)
                    output_directory = "../currated"
                    print("calling move_these_files (" + file + ", "  +output_directory + ", " + sub_directory)
                    move_these_files(file, output_directory, sub_directory)
                    print("move_these_files complete")
                print()
    print("Done Processing directory:", root)
    if "_" in root and "nsfw" not in root:
        input_directory = root
        output_directory = "../currated"
        sub_directory = os.path.basename(root)
        #move_files(input_directory, output_directory, sub_directory)

delete_empty_subdirectories(root_directory)
print("finishing qa.py")
