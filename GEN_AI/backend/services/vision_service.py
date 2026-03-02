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
        
        # All COCO animal classes treated as valid "pets" / roastable subjects.
        # Covers: common pets, farm animals, wild animals — anything alive.
        self.PET_CLASSES = {
            "bird", "cat", "dog", "horse", "sheep", "cow",
            "elephant", "bear", "zebra", "giraffe",
        }
        # Low threshold so we catch partially-visible or small pets.
        # We compensate for false positives by taking the BEST score across
        # multiple frames and multiple blob sizes (see detect_best_pet).
        self.CONFIDENCE_THRESHOLD = 0.05

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

    def _yolo_run_all(self, image_bgr, blob_size: int) -> dict[str, float]:
        """Run YOLO on one image at one blob size.
        Returns a dict of {pet_label: best_confidence} for EVERY pet class
        found above CONFIDENCE_THRESHOLD (not just the top-1)."""
        ln = self.net.getLayerNames()
        out_layers = self.net.getUnconnectedOutLayers()
        flat = out_layers.flatten() if isinstance(out_layers, np.ndarray) else [x[0] for x in out_layers]
        ln = [ln[i - 1] for i in flat]

        blob = cv2.dnn.blobFromImage(
            image_bgr, 1 / 255.0, (blob_size, blob_size), swapRB=True, crop=False
        )
        self.net.setInput(blob)
        layer_outputs = self.net.forward(ln)

        found: dict[str, float] = {}
        for output in layer_outputs:
            for detection in output:
                scores = detection[5:]
                for cid, label in enumerate(self.CLASSES):
                    if label in self.PET_CLASSES:
                        conf = float(scores[cid])
                        if conf >= self.CONFIDENCE_THRESHOLD:
                            if conf > found.get(label, 0.0):
                                found[label] = conf
        return found

    def _yolo_run(self, image_bgr, blob_size: int) -> tuple[str | None, float]:
        """Convenience wrapper — returns the single highest-confidence pet
        from _yolo_run_all (used by detect_best_pet)."""
        found = self._yolo_run_all(image_bgr, blob_size)
        if not found:
            return None, 0.0
        best_label = max(found, key=lambda k: found[k])
        return best_label, found[best_label]

    @staticmethod
    def _add_letterbox(image_bgr, pad_pct: float):
        """Add grey border padding so close-up pets appear smaller in frame,
        making YOLO anchor boxes more likely to match."""
        h, w = image_bgr.shape[:2]
        ph, pw = int(h * pad_pct), int(w * pad_pct)
        return cv2.copyMakeBorder(
            image_bgr, ph, ph, pw, pw,
            cv2.BORDER_CONSTANT, value=(114, 114, 114)
        )

    def detect_best_pet(self, image_bgr) -> tuple[str | None, float]:
        """
        Two-pass detection strategy:
        Pass 1 — normal image at blob sizes 320, 416, 608.
                  Checks ALL pet class scores per detection box (not just argmax).
        Pass 2 — letterboxed image (10 / 20 / 35 / 50 % border padding) at
                  416 and 608.  Helps when the pet fills the entire frame and
                  YOLO's anchor boxes cannot fire at normal scale.
        Returns (pet_label, confidence) or (None, 0.0) if nothing found.
        """
        if self.net is None:
            return None, 0.0

        best_label: str | None = None
        best_conf: float = 0.0

        # --- Pass 1: normal image, three blob sizes ---
        for blob_size in (320, 416, 608):
            lbl, conf = self._yolo_run(image_bgr, blob_size)
            if lbl and conf > best_conf:
                best_conf = conf
                best_label = lbl

        if best_label:
            return best_label, best_conf

        # --- Pass 2: letterbox padding — close-up recovery ---
        for pad_pct in (0.10, 0.20, 0.35, 0.50):
            padded = self._add_letterbox(image_bgr, pad_pct)
            for blob_size in (416, 608):
                lbl, conf = self._yolo_run(padded, blob_size)
                if lbl and conf > best_conf:
                    best_conf = conf
                    best_label = lbl

        return best_label, best_conf

    def detect_all_pets(self, image_bgr) -> dict[str, float]:
        """
        Multi-species variant of detect_best_pet.
        Returns a dict of {pet_label: best_confidence} for EVERY distinct pet
        species visible in the frame (e.g. {'dog': 0.71, 'cat': 0.45}).

        Same two-pass strategy as detect_best_pet:
        Pass 1 — normal image at 320 / 416 / 608.
        Pass 2 — letterbox padding (10-50 %) at 416 / 608 if Pass 1 found
                  fewer than 2 species (to catch close-up single pets).
        """
        if self.net is None:
            return {}

        merged: dict[str, float] = {}

        # --- Pass 1: normal image, three blob sizes ---
        for blob_size in (320, 416, 608):
            for lbl, conf in self._yolo_run_all(image_bgr, blob_size).items():
                if conf > merged.get(lbl, 0.0):
                    merged[lbl] = conf

        # --- Pass 2: letterbox — only if fewer than 2 species found so far ---
        if len(merged) < 2:
            for pad_pct in (0.10, 0.20, 0.35, 0.50):
                padded = self._add_letterbox(image_bgr, pad_pct)
                for blob_size in (416, 608):
                    for lbl, conf in self._yolo_run_all(padded, blob_size).items():
                        if conf > merged.get(lbl, 0.0):
                            merged[lbl] = conf

        return merged

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
