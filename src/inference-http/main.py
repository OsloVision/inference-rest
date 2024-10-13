from flask import Flask, request, jsonify
from PIL import Image
import io
from ultralytics import YOLO
import logging
from logging.handlers import RotatingFileHandler
import sys
import time

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
handler = RotatingFileHandler("app.log", maxBytes=10000, backupCount=1)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.addHandler(logging.StreamHandler(sys.stdout))

# Load the YOLOv11 model
try:
    model = YOLO("./bikeweights.pt")
    app.logger.info("YOLOv11 model loaded successfully")
except Exception as e:
    app.logger.error(f"Failed to load YOLOv11 model: {str(e)}")


@app.route("/up", methods=["GET"])
def up():
    return "Service is up and running"


@app.route("/predict", methods=["POST"])
def predict():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected for uploading"}), 400

    if file:
        # Read the image file
        img_bytes = file.read()
        img = Image.open(io.BytesIO(img_bytes))

        # Perform inference and measure time
        start_time = time.time()
        results = model(img)
        inference_time = time.time() - start_time

        # Process results
        detections = []
        for result in results:
            boxes = (
                result.boxes.xyxy.tolist()
            )  # get box coordinates in (top, left, bottom, right) format
            classes = result.boxes.cls.tolist()  # get class labels
            confidences = result.boxes.conf.tolist()  # get confidence scores

            for box, cls, conf in zip(boxes, classes, confidences):
                detections.append(
                    {"box": box, "class": model.names[int(cls)], "confidence": conf}
                )

        return jsonify({"detections": detections, "inference_time": inference_time})


if __name__ == "__main__":
    app.run(debug=True)
