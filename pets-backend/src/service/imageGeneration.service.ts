import axios from 'axios';
import { ImageGeneration } from '../model/imageGenerationSchema';
import { logger } from '../utils/logger';
import { uploadToR2 } from '../utils/s3Config';

export class ImageGenerationService {
    private readonly petRoastApiUrl = process.env.PET_ROAST_API_URL || 'http://localhost:8000/api';

    async generateImage(userId: string, prompt: string, imageBuffer: Buffer, fileName: string, mimeType: string) {
        logger.info(`🔄 Initiating video roast for userId: ${userId}`);

        try {
            // 1. Upload to Cloudflare R2
            const imageUrl = await uploadToR2(imageBuffer, fileName, mimeType);

            // 2. Create a record in MongoDB
            const generationRecord = await ImageGeneration.create({
                userId,
                prompt,
                inputImageLink: imageUrl,
                status: 'processing',
            });

            // 3. Call Pet Roast AI Service (FastAPI)
            logger.info(`📡 Calling AI service at: ${this.petRoastApiUrl}/generate-video`);
            const response = await axios.post(`${this.petRoastApiUrl}/generate-video`, {
                text: prompt,
                image_url: imageUrl
            }, {
                headers: { 'Content-Type': 'application/json' }
            });

            const { job_id, status } = response.data;

            if (!job_id) {
                throw new Error("Failed to get job_id from AI service");
            }

            // 4. Update Record with job ID
            generationRecord.jobId = job_id;
            generationRecord.status = status || 'processing';
            await generationRecord.save();

            logger.info(`✅ Video generation job initiated. Job ID: ${job_id}`);

            return {
                jobId: job_id,
                status: generationRecord.status,
                inputImageUrl: imageUrl
            };
        } catch (error: any) {
            logger.error(`❌ Video generation initiation failed: ${error.message}`);
            if (error.response) {
                logger.error(`AI Service response: ${JSON.stringify(error.response.data)}`);
            }
            throw error;
        }
    }

    async getJobStatus(jobId: string) {
        try {
            // 1. Check DB first
            const record = await ImageGeneration.findOne({ jobId });

            if (record && record.status === 'completed' && record.outputVideoUrl) {
                logger.info(`✅ Job ${jobId} already completed in DB`);
                return {
                    job_id: record.jobId,
                    status: record.status,
                    video_url: record.outputVideoUrl,
                    created_at: record.createdAt
                };
            }

            // 2. If not completed in DB, check 3rd party API
            logger.info(`📡 Checking API status for job: ${jobId}`);
            const response = await axios.get(`${this.petRoastApiUrl}/video-status/${jobId}`);
            const data = response.data;

            // 3. Update DB if status changed
            if (record && data.status && record.status !== data.status) {
                record.status = data.status;
                if (data.status === 'completed' && data.video_url) {
                    record.outputVideoUrl = data.video_url;
                }
                await record.save();
                logger.info(`💾 Updated job ${jobId} status to ${data.status} in DB`);
            }

            return data;
        } catch (error: any) {
            logger.error(`❌ Error fetching job status for ${jobId}: ${error.message}`);
            throw error;
        }
    }

    async getJobResult(jobId: string) {
        try {
            const response = await axios.get(`${this.petRoastApiUrl}/video-result/${jobId}`);
            return response.data;
        } catch (error: any) {
            logger.error(`❌ Error fetching job result for ${jobId}: ${error.message}`);
            throw error;
        }
    }
}
