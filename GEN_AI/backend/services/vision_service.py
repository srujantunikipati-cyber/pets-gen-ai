import cv2
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)

class VisionService:
    def __init__(self):
        self.models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
        self.cfg = os.path.join(self.models_dir, "yolov3-tiny.cfg")
        self.weights = os.path.join(self.models_dir, "yolov3-tiny.weights")
        
        self.net = None
        
        # 80 COCO Classes
        self.CLASSES = [
            "person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck",
            "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
            "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe",
            "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard",
            "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard",
            "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl",
            "banana", "apple", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza",
            "donut", "cake", "chair", "sofa", "pottedplant", "bed", "diningtable", "toilet",
            "tvmonitor", "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave",
            "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors",
            "teddy bear", "hair drier", "toothbrush"
        ]
        
        # Classes we consider as valid "pets" or roastable subjects
        self.PET_CLASSES = {"bird", "cat", "dog", "horse", "sheep", "cow"}
        self.CONFIDENCE_THRESHOLD = 0.25  # Tiny YOLO needs a slightly lower threshold for good recall
        
        self._load_model()

    def _load_model(self):
        try:
            if not os.path.exists(self.cfg) or not os.path.exists(self.weights):
                logger.error("OpenCV YOLOv3-tiny model files not found in models/ directory!")
                return
            
            logger.info("Loading OpenCV DNN YOLOv3-tiny model for pet detection...")
            self.net = cv2.dnn.readNetFromDarknet(self.cfg, self.weights)
            
            # Try to use GPU if OpenVINO or CUDA is available natively in OpenCV
            self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            logger.info("OpenCV DNN model loaded successfully.")
            
        except Exception as e:
            logger.error(f"Failed to load OpenCV YOLO model: {e}")

    async def detect_pet_in_image(self, image_path: str) -> bool:
        """
        Uses OpenCV YOLOv3-tiny to detect if a pet/animal is in the image.
        Returns True if a valid pet class is detected with confidence > Threshold.
        """
        if self.net is None:
            logger.warning("Vision model not loaded, failing safe (False).")
            return False
            
        try:
            logger.info(f"Running OpenCV YOLOv3-tiny on frame: {image_path}")
            
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                raise Exception(f"Failed to read image at {image_path}")
                
            (H, W) = image.shape[:2]
            
            # Get the output layer names
            ln = self.net.getLayerNames()
            out_layers = self.net.getUnconnectedOutLayers()
            if isinstance(out_layers, np.ndarray):
                ln = [ln[i - 1] for i in out_layers]
            else:
                ln = [ln[i[0] - 1] for i in out_layers]
            
            # Preprocess image into a blob
            blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416), swapRB=True, crop=False)
            
            self.net.setInput(blob)
            layerOutputs = self.net.forward(ln)
            
            detected_pets = []
            
            # Loop over detections
            for output in layerOutputs:
                for detection in output:
                    scores = detection[5:]
                    class_id = np.argmax(scores)
                    confidence = scores[class_id]
                    
                    if confidence > self.CONFIDENCE_THRESHOLD:
                        if class_id < len(self.CLASSES):
                            label = self.CLASSES[class_id]
                            if label in self.PET_CLASSES:
                                logger.info(f"OpenCV YOLO Detected: {label} (confidence: {confidence:.2f})")
                                detected_pets.append(label)
                            
            if detected_pets:
                logger.info(f"Pet verification PASSED: Found {', '.join(set(detected_pets))}")
                return True
                
            logger.info("Pet verification FAILED: No pets found in the frame.")
            return False
            
        except Exception as e:
            logger.error(f"OpenCV pet detection failed: {e}")
            raise Exception(f"Vision detection failed: {str(e)}")
