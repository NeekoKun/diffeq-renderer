import tqdm
import cv2
import os

image_files = ["frame_"+str(i)+".png" for i in range(240)]
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
video_writer = cv2.VideoWriter("render2.avi", fourcc, 60, (1920, 1200))

for image_file in tqdm.tqdm(image_files):
    image_path = os.path.join("frames", image_file)
    image = cv2.imread(image_path)
    video_writer.write(image)

video_writer.release()