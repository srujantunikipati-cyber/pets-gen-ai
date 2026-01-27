import { Router, Request, Response } from 'express';
import multer from 'multer';
import { ImageGenerationService } from '../service/imageGeneration.service';
import { logger } from '../utils/logger';
import { ImageGeneration } from '../model/imageGenerationSchema';
import { PetRoastJob } from '../model/petRoastJobSchema';

const router = Router();
const upload = multer(); // Memory storage to handle files as buffers
const imageService = new ImageGenerationService();

/**
 * @route GET /api/image/:id
 * @desc Serves the input image from MongoDB
 */
router.get('/image/:id', async (req: Request, res: Response) => {
    try {
        const { id } = req.params;

        // Try finding in ImageGeneration collection
        let record: any = await ImageGeneration.findById(id);

        // If not found, try PetRoastJob collection
        if (!record) {
            record = await PetRoastJob.findById(id);
        }

        if (!record || !record.inputImageBuffer) {
            logger.warn(`⚠️ Image not found in DB for ID: ${id}`);
            return res.status(404).send('Image not found');
        }

        res.set('Content-Type', record.inputImageMimeType || 'image/jpeg');
        return res.send(record.inputImageBuffer);
    } catch (error: any) {
        logger.error(`❌ Error in /image/:id route: ${error.message}`);
        return res.status(500).send('Internal Server Error');
    }
});

/**
 * @route POST /api/generate-image
 * @desc Accepts prompt, userId, and image file, calls Modal API, returns generated image.
 */
router.post('/generate-image', upload.single('image'), async (req: Request, res: Response) => {
    try {
        const { prompt, userId } = req.body;
        const file = req.file;

        if (!prompt || !userId || !file) {
            return res.status(400).json({
                success: false,
                message: 'Missing required fields: prompt, userId, or image'
            });
        }

        logger.info(`📥 Received image generation request for userId: ${userId}`);

        const result = await imageService.generateImage(
            userId,
            prompt,
            file.buffer,
            file.originalname,
            file.mimetype
        );

        // Return the job details as JSON
        return res.status(202).json({
            success: true,
            jobId: result.jobId,
            status: result.status,
            inputImageUrl: result.inputImageUrl,
            message: 'Video generation job initiated successfully'
        });

    } catch (error: any) {
        logger.error(`❌ Error in /generate-image route: ${error.message}`);
        return res.status(500).json({
            success: false,
            message: error.message || 'Internal Server Error'
        });
    }
});

/**
 * @route GET /api/get-video/:jobId
 * @desc Polling route to check video status and get results
 */
router.get('/get-video/:jobId', async (req: Request, res: Response) => {
    try {
        const { jobId } = req.params;

        // 1. Check status from AI service
        const statusData = await imageService.getJobStatus(jobId);

        // 2. If completed, fetch final result
        if (statusData.status === 'completed') {
            const resultData = await imageService.getJobResult(jobId);

            // 3. Update local database record
            await ImageGeneration.findOneAndUpdate(
                { jobId },
                {
                    status: 'completed',
                    outputImageLink: resultData.video_url // Reusing outputImageLink for video or adding videoUrl
                },
                { new: true }
            );

            return res.json({
                success: true,
                status: 'completed',
                videoUrl: resultData.video_url
            });
        }

        return res.json({
            success: true,
            status: statusData.status,
            message: 'Video generation still in progress'
        });

    } catch (error: any) {
        logger.error(`❌ Error in /get-video/:jobId route: ${error.message}`);
        return res.status(500).json({
            success: false,
            message: error.message || 'Internal Server Error'
        });
    }
});

export default router;
