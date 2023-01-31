import torch
import os
import shutil

print(
    f"Setup complete. Using torch {torch.__version__} ({torch.cuda.get_device_properties(0).name if torch.cuda.is_available() else 'CPU'})")


weights = "weights/best.pt"
data = "data.yaml"
if (os.path.exists("yolov5/runs")):
    shutil.rmtree("yolov5/runs")
os.system(
    f"python yolov5/train.py --img 416 --batch 32 --epochs 100 --data {data} --weights {weights} --cache")
shutil.copy("yolov5/runs/train/exp/weights/best.pt", "weights/best.pt")
