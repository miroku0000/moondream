import os
import time
from moondream import Moondream, detect_device, LATEST_REVISION
from transformers import AutoTokenizer
from PIL import Image
import shutil

import os
import shutil

def delete_empty_subdirectories(root_dir):
    # Walk through all directories and subdirectories in the root_dir
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
        # Check if the directory is empty
        if not any(filenames):
            # Delete the empty directory
            shutil.rmtree(dirpath)
            print(f"Deleted empty directory: {dirpath}")

# Specify the root directory
root_directory = "../output"




device, dtype = detect_device()

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

                prompts = [
                    #"Answer with an integer only: how many people are in the picture?",
                    "Answer yes or no: is everyone wearing a top?",
                    #"Answer only yes or no: could this be from the medieval era?",
                    #"Answer only male or female: What is the gender of the person in the picture",
                    "On a scale of 1-10, how much does this look like a single person who is a " + desc,
                    ]
                if "dwarf" in desc:
                    prompts.append("Answer yes or no: does this person have a beard?")
                if "dwarf" in desc:
                    prompts.append("Answer yes or no: Is this person over 1 foot tall?")


                images=[] 
                while len(images) < len(prompts):
                    images.append(image)

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

                # Extract answers
                index=0
                #people_count = int(answers[index])
                #index=index+1
                nudity_score = answers[index].lower()
                index=index+1
                #medieval_era = answers[index].lower()
                #index=index+1
                #gender = answers[index].lower()
                #index=index+1
                accuracy = int(answers[index].lower())
                index=index+1
                if "dwarf" in desc:
                    beard = answers[index].lower()
                    index=index+1
                if "dwarf" in desc:
                    height = answers[index].lower()
                    index=index+1



                print(f"File: {file_path}")
                #print(f"Number of people: {people_count}")
                print(f"Is everyone wearing a top {nudity_score}")
                #print(f"Medieval looking: {medieval_era}")
                #print(f"gender: {gender}")
                print(f"accuracy: {accuracy}")
                #print(f"gender: {gender}")
                if "dwarf" in desc:
                    print(f"beard: {beard}")
                    print(f"height: {height}")
                
                
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
                elif accuracy <8:
                    print("Deleting due to low accuracy")
                    os.remove(file_path)
                    # Delete corresponding JSON file
                    json_file = os.path.splitext(file)[0] + ".json"
                    json_file_path = os.path.join(root, json_file)
                    if os.path.exists(json_file_path):
                        os.remove(json_file_path)
                elif beard== "no" and "dwarf" in desc:
                    print("Deleting due to no dwarfs without beards")
                    os.remove(file_path)
                    # Delete corresponding JSON file
                    json_file = os.path.splitext(file)[0] + ".json"
                    json_file_path = os.path.join(root, json_file)
                    if os.path.exists(json_file_path):
                        os.remove(json_file_path)
                elif height == "no" and "dwarf" in desc:
                    print("Deleting due to no <1 foot tall  dwarfs")
                    os.remove(file_path)
                    # Delete corresponding JSON file
                    json_file = os.path.splitext(file)[0] + ".json"
                    json_file_path = os.path.join(root, json_file)
                    if os.path.exists(json_file_path):
                        os.remove(json_file_path)
                
                # elif people_count != 1:
                #     print("Deleting the image because the number of people is not 1.")
                #     os.remove(file_path)
                #     # Delete corresponding JSON file
                #     json_file = os.path.splitext(file)[0] + ".json"
                #     json_file_path = os.path.join(root, json_file)
                #     if os.path.exists(json_file_path):
                #         os.remove(json_file_path)
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
