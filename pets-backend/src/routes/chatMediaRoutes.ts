import { Router, Request, Response } from "express";
import multer from "multer";
import {
    compressImage,
    generateImageThumbnail,
    validateImage,
    validateVideo,
    validateFile,
} from "../utils/mediaProcessor";
import {
    uploadImageWithThumbnail,
    uploadVideo,
    uploadFile,
} from "../utils/chatMediaStorage";
import { logger } from "../utils/logger";

const router = Router();

// Configure multer for memory storage
const upload = multer({
    storage: multer.memoryStorage(),
    limits: {
        fileSize: 50 * 1024 * 1024, // 50MB max
    },
});

/**
 * POST /api/chat/upload/image
 * Upload an image for chat
 */
router.post("/upload/image", upload.single("image"), async (req: Request, res: Response) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: "No image file provided" });
        }

        const { userId, conversationId } = req.body;

        if (!userId || !conversationId) {
            return res.status(400).json({ error: "userId and conversationId are required" });
        }

        // Validate image
        await validateImage(req.file.buffer, 5 * 1024 * 1024); // 5MB max for images

        // Compress image
        const compressed = await compressImage(req.file.buffer);

        // Generate thumbnail
        const thumbnail = await generateImageThumbnail(req.file.buffer);

        // Upload to R2
        const result = await uploadImageWithThumbnail(
            compressed.buffer,
            thumbnail.buffer,
            req.file.originalname,
            compressed.mimeType,
            userId,
            conversationId
        );

        logger.info(`✅ Image uploaded successfully for user ${userId}`);

        res.json({
            success: true,
            data: {
                imageUrl: result.imageUrl,
                thumbnailUrl: result.thumbnailUrl,
                size: result.imageSize,
                width: compressed.width,
                height: compressed.height,
            },
        });
    } catch (error: any) {
        logger.error(`❌ Image upload error: ${error.message}`);
        res.status(500).json({ error: error.message || "Failed to upload image" });
    }
});

/**
 * POST /api/chat/upload/video
 * Upload a video for chat
 */
router.post("/upload/video", upload.single("video"), async (req: Request, res: Response) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: "No video file provided" });
        }

        const { userId, conversationId } = req.body;

        if (!userId || !conversationId) {
            return res.status(400).json({ error: "userId and conversationId are required" });
        }

        // Validate video
        validateVideo(req.file.mimetype, req.file.size, 50 * 1024 * 1024); // 50MB max

        // Upload to R2
        const result = await uploadVideo(
            req.file.buffer,
            req.file.originalname,
            req.file.mimetype,
            userId,
            conversationId
        );

        logger.info(`✅ Video uploaded successfully for user ${userId}`);

        res.json({
            success: true,
            data: {
                videoUrl: result.url,
                size: result.size,
            },
        });
    } catch (error: any) {
        logger.error(`❌ Video upload error: ${error.message}`);
        res.status(500).json({ error: error.message || "Failed to upload video" });
    }
});

/**
 * POST /api/chat/upload/file
 * Upload a general file for chat
 */
router.post("/upload/file", upload.single("file"), async (req: Request, res: Response) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: "No file provided" });
        }

        const { userId, conversationId } = req.body;

        if (!userId || !conversationId) {
            return res.status(400).json({ error: "userId and conversationId are required" });
        }

        // Validate file
        validateFile(req.file.mimetype, req.file.size, 10 * 1024 * 1024); // 10MB max

        // Upload to R2
        const result = await uploadFile(
            req.file.buffer,
            req.file.originalname,
            req.file.mimetype,
            userId,
            conversationId
        );

        logger.info(`✅ File uploaded successfully for user ${userId}`);

        res.json({
            success: true,
            data: {
                fileUrl: result.url,
                fileName: req.file.originalname,
                fileType: req.file.mimetype,
                size: result.size,
            },
        });
    } catch (error: any) {
        logger.error(`❌ File upload error: ${error.message}`);
        res.status(500).json({ error: error.message || "Failed to upload file" });
    }
});

export default router;
