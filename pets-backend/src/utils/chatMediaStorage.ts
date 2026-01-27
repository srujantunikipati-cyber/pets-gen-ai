import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";
import { logger } from "./logger";

const r2Endpoint = process.env.CLOUDFLARE_R2_ENDPOINT || "";
const r2AccessKeyId = process.env.CLOUDFLARE_R2_ACCESS_KEY_ID || "";
const r2SecretAccessKey = process.env.CLOUDFLARE_R2_SECRET_ACCESS_KEY || "";
const r2BucketName = process.env.CLOUDFLARE_R2_BUCKET_NAME || "";
const r2PublicDomain = process.env.CLOUDFLARE_R2_PUBLIC_DOMAIN || "";

const s3Client = new S3Client({
    region: "auto",
    endpoint: r2Endpoint,
    credentials: {
        accessKeyId: r2AccessKeyId,
        secretAccessKey: r2SecretAccessKey,
    },
});

export interface MediaUploadResult {
    url: string;
    key: string;
    size: number;
}

/**
 * Uploads chat media (image, video, file) to Cloudflare R2
 * @param buffer - File buffer
 * @param fileName - Original file name
 * @param mimeType - File MIME type
 * @param userId - User ID for organizing files
 * @param conversationId - Conversation ID for organizing files
 * @param mediaType - Type of media (image, video, file)
 * @returns Upload result with URL and metadata
 */
export async function uploadChatMedia(
    buffer: Buffer,
    fileName: string,
    mimeType: string,
    userId: string,
    conversationId: string,
    mediaType: "image" | "video" | "file" | "thumbnail"
): Promise<MediaUploadResult> {
    if (!r2BucketName) {
        throw new Error("CLOUDFLARE_R2_BUCKET_NAME is not defined");
    }

    // Organize files: chat-media/{userId}/{conversationId}/{mediaType}/{timestamp}-{filename}
    const timestamp = Date.now();
    const sanitizedFileName = fileName.replace(/[^a-zA-Z0-9.-]/g, "_");
    const key = `chat-media/${userId}/${conversationId}/${mediaType}/${timestamp}-${sanitizedFileName}`;

    try {
        const command = new PutObjectCommand({
            Bucket: r2BucketName,
            Key: key,
            Body: buffer,
            ContentType: mimeType,
            // Set cache control for better performance
            CacheControl: "public, max-age=31536000", // 1 year
        });

        await s3Client.send(command);

        // Construct the public URL
        const url = r2PublicDomain
            ? `${r2PublicDomain}/${key}`
            : `${r2Endpoint}/${r2BucketName}/${key}`;

        logger.info(`✅ Chat media uploaded to R2: ${url}`);

        return {
            url,
            key,
            size: buffer.length,
        };
    } catch (error: any) {
        logger.error(`❌ R2 Upload Error: ${error.message}`);
        throw new Error("Failed to upload media to storage");
    }
}

/**
 * Uploads an image with thumbnail to R2
 * @param imageBuffer - Compressed image buffer
 * @param thumbnailBuffer - Thumbnail buffer
 * @param fileName - Original file name
 * @param mimeType - Image MIME type
 * @param userId - User ID
 * @param conversationId - Conversation ID
 * @returns Object with image URL and thumbnail URL
 */
export async function uploadImageWithThumbnail(
    imageBuffer: Buffer,
    thumbnailBuffer: Buffer,
    fileName: string,
    mimeType: string,
    userId: string,
    conversationId: string
): Promise<{ imageUrl: string; thumbnailUrl: string; imageSize: number }> {
    try {
        // Upload main image
        const imageResult = await uploadChatMedia(
            imageBuffer,
            fileName,
            mimeType,
            userId,
            conversationId,
            "image"
        );

        // Upload thumbnail
        const thumbnailResult = await uploadChatMedia(
            thumbnailBuffer,
            `thumb_${fileName}`,
            "image/jpeg",
            userId,
            conversationId,
            "thumbnail"
        );

        return {
            imageUrl: imageResult.url,
            thumbnailUrl: thumbnailResult.url,
            imageSize: imageResult.size,
        };
    } catch (error: any) {
        logger.error(`❌ Image upload with thumbnail error: ${error.message}`);
        throw error;
    }
}

/**
 * Uploads a video to R2
 * @param videoBuffer - Video buffer
 * @param fileName - Original file name
 * @param mimeType - Video MIME type
 * @param userId - User ID
 * @param conversationId - Conversation ID
 * @returns Upload result
 */
export async function uploadVideo(
    videoBuffer: Buffer,
    fileName: string,
    mimeType: string,
    userId: string,
    conversationId: string
): Promise<MediaUploadResult> {
    return uploadChatMedia(videoBuffer, fileName, mimeType, userId, conversationId, "video");
}

/**
 * Uploads a general file to R2
 * @param fileBuffer - File buffer
 * @param fileName - Original file name
 * @param mimeType - File MIME type
 * @param userId - User ID
 * @param conversationId - Conversation ID
 * @returns Upload result
 */
export async function uploadFile(
    fileBuffer: Buffer,
    fileName: string,
    mimeType: string,
    userId: string,
    conversationId: string
): Promise<MediaUploadResult> {
    return uploadChatMedia(fileBuffer, fileName, mimeType, userId, conversationId, "file");
}
