import json
import time
import subprocess
from pathlib import Path
from video import extract_frames
import pprint


def describe_frame(frame_number: int, 
                   image_file: Path, 
                   questions: list[str]):
    if not image_file.exists():
        raise ValueError(f"No image exists at {image_file.absolute()}")

    model_path = "liuhaotian/llava-v1.5-7b"
    command = [
        "python3", "-W ignore", "-m",  
        "llava.serve.cli",
        "--model-path", model_path,
        "--image-file", image_file
    ]
    command.append("--load-4bit")
    
    answers = {}

    answers['frame_number'] = frame_number
    answers['questions'] = []

    for question in questions:
        result = subprocess.run(command, input=question, stdout=subprocess.PIPE, text=True)
        result = result.stdout
        split_result = result.split("ASSISTANT:")

        actual_response = split_result[1].strip()
        if actual_response.find("USER:") != -1:
            user_index = actual_response.find("USER:")
            actual_response = actual_response[:user_index]

        actual_response = actual_response.strip()
        answers['questions'].append({'prompt': question, 'answer': actual_response})
    
    return answers


def describe_video(questions: list[str], 
                   video_path: Path, 
                   frame_dir: Path, 
                   k: int = 10):
    if not video_path.exists():
        raise ValueError(f"Provided file path {video_path} does not exist")
    
    extract_frames(video_path, frame_dir, k)
    images = []

    for frame in sorted(frame_dir.iterdir()):
        print(f"\n\nprocessing {frame.name}...\n")
        frame_num = int(frame.name[frame.name.find('frame')+5:frame.name.find('.')])
        current_frame = describe_frame(frame_num, frame, questions)
        images.append(current_frame)

    answer = {
        'video_name': video_path.name,
        'frames': images
    }

    return answer
        

def process_videos(video_dir: Path, 
                   questions: list[str],
                   output_file: Path,
                   k: int = 10):
    if not video_dir.exists():
        raise ValueError(f"Provided file path {video_dir} does not exist")

    answers = []
    for video in sorted(video_dir.iterdir()):
        print(f"\n\nprocessing {video.name}..")
        if video.suffix in ['.mp4']:
            frame_dir = Path("extracted-frames") / video.name
            answers.append(describe_video(questions, video, frame_dir, k))

        with open(output_file, 'w') as f:
            json.dump(answers, f, indent=4) 

    return answers


if __name__ == "__main__":
    start = time.time()    

    output_file = Path("data.json")
    video_dir = Path("custom-videos")

    questions = [
        "Provide a detailed description of the food you see in the image.",
        "Provide a detailed list of cutlery the person in the image is eating with. Just a list should suffice, don't bother including other details."
        "Provide a detailed list of all utensils and cutlery in the image. Just a list should suffice, don't bother including other details."
        "Provide a detailed list of the ingredients of the food in the image. Only include a comma-separated list of items with no additional descriptions for each item in your response.",
        "Provide an approximate estimate the weight of the food in the image in grams. It is completely okay if your estimate is off, all I care about is getting an estimate. Only provide a number and the unit in your response."
    ]

    process_videos(video_dir, questions, output_file, k = 10)
    
    # sample_video = Path("extracted-frames/5.mp4/frame20.jpg")
    # sample_video = Path("custom-images/broccoli.png")

    # # two variants: all in image vs only those eating with
    # questions = [
    #     "Provide a detailed list of cutlery the person in the image is eating with. Just a list should suffice, don't bother including other details."
    #     "Provide a detailed list of all utensils and cutlery in the image. Just a list should suffice, don't bother including other details."
    # ]
    # response = describe_frame(20, sample_video, questions)
    # pprint.pprint(response)

    # end = time.time()    
    # print(f"\n{round(end - start, 2)} seconds elapsed...")