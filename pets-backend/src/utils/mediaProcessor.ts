// Try to import sharp, but make it optional
let sharp: any;
try {
    sharp = require("sharp");
} catch (error) {
    console.warn("⚠️  Sharp module not available. Image processing features will be disabled.");
    console.warn("   To enable image processing, ensure you're using Node.js 18+ and run: npm rebuild sharp");
}

import { logger } from "./logger";

export interface ImageProcessingResult {
    buffer: Buffer;
    mimeType: string;
    width: number;
    height: number;
}

export interface ThumbnailResult {
    buffer: Buffer;
    mimeType: string;
}

/**
 * Compresses an image while maintaining quality
 * @param buffer - Original image buffer
 * @param maxWidth - Maximum width (default: 1920)
 * @param maxHeight - Maximum height (default: 1080)
 * @returns Compressed image buffer and metadata
 */
export async function compressImage(
    buffer: Buffer,
    maxWidth: number = 1920,
    maxHeight: number = 1080
): Promise<ImageProcessingResult> {
    try {
        const image = sharp(buffer);
        const metadata = await image.metadata();

        // Resize if image is larger than max dimensions
        let processedImage = image;
        if (metadata.width && metadata.width > maxWidth || metadata.height && metadata.height > maxHeight) {
            processedImage = image.resize(maxWidth, maxHeight, {
                fit: "inside",
                withoutEnlargement: true,
            });
        }

        // Compress based on format
        const format = metadata.format || "jpeg";
        let outputBuffer: Buffer;
        let mimeType: string;

        switch (format) {
            case "png":
                outputBuffer = await processedImage.png({ quality: 80, compressionLevel: 9 }).toBuffer();
                mimeType = "image/png";
                break;
            case "webp":
                outputBuffer = await processedImage.webp({ quality: 80 }).toBuffer();
                mimeType = "image/webp";
                break;
            default:
                outputBuffer = await processedImage.jpeg({ quality: 80 }).toBuffer();
                mimeType = "image/jpeg";
        }

        const processedMetadata = await sharp(outputBuffer).metadata();

        logger.info(`✅ Image compressed: ${metadata.width}x${metadata.height} → ${processedMetadata.width}x${processedMetadata.height}`);

        return {
            buffer: outputBuffer,
            mimeType,
            width: processedMetadata.width || 0,
            height: processedMetadata.height || 0,
        };
    } catch (error: any) {
        logger.error(`❌ Image compression error: ${error.message}`);
        throw new Error("Failed to compress image");
    }
}

/**
 * Generates a thumbnail from an image
 * @param buffer - Original image buffer
 * @param size - Thumbnail size (default: 200x200)
 * @returns Thumbnail buffer
 */
export async function generateImageThumbnail(
    buffer: Buffer,
    size: number = 200
): Promise<ThumbnailResult> {
    try {
        const thumbnailBuffer = await sharp(buffer)
            .resize(size, size, {
                fit: "cover",
                position: "center",
            })
            .jpeg({ quality: 70 })
            .toBuffer();

        logger.info(`✅ Thumbnail generated: ${size}x${size}`);

        return {
            buffer: thumbnailBuffer,
            mimeType: "image/jpeg",
        };
    } catch (error: any) {
        logger.error(`❌ Thumbnail generation error: ${error.message}`);
        throw new Error("Failed to generate thumbnail");
    }
}

/**
 * Validates image file type and size
 * @param buffer - Image buffer
 * @param maxSize - Maximum file size in bytes (default: 5MB)
 * @returns true if valid, throws error otherwise
 */
export async function validateImage(buffer: Buffer, maxSize: number = 5 * 1024 * 1024): Promise<boolean> {
    if (buffer.length > maxSize) {
        throw new Error(`Image size exceeds maximum of ${maxSize / (1024 * 1024)}MB`);
    }

    try {
        const metadata = await sharp(buffer).metadata();
        const allowedFormats = ["jpeg", "jpg", "png", "webp", "gif"];

        if (!metadata.format || !allowedFormats.includes(metadata.format)) {
            throw new Error(`Invalid image format. Allowed: ${allowedFormats.join(", ")}`);
        }

        return true;
    } catch (error: any) {
        logger.error(`❌ Image validation error: ${error.message}`);
        throw new Error("Invalid image file");
    }
}

/**
 * Validates video file type and size
 * @param mimeType - Video MIME type
 * @param fileSize - File size in bytes
 * @param maxSize - Maximum file size in bytes (default: 50MB)
 * @returns true if valid, throws error otherwise
 */
export function validateVideo(mimeType: string, fileSize: number, maxSize: number = 50 * 1024 * 1024): boolean {
    const allowedMimeTypes = ["video/mp4", "video/webm", "video/ogg", "video/quicktime"];

    if (!allowedMimeTypes.includes(mimeType)) {
        throw new Error(`Invalid video format. Allowed: ${allowedMimeTypes.join(", ")}`);
    }

    if (fileSize > maxSize) {
        throw new Error(`Video size exceeds maximum of ${maxSize / (1024 * 1024)}MB`);
    }

    return true;
}

/**
 * Validates general file type and size
 * @param mimeType - File MIME type
 * @param fileSize - File size in bytes
 * @param maxSize - Maximum file size in bytes (default: 10MB)
 * @returns true if valid, throws error otherwise
 */
export function validateFile(mimeType: string, fileSize: number, maxSize: number = 10 * 1024 * 1024): boolean {
    // Blacklist dangerous file types
    const dangerousMimeTypes = [
        "application/x-msdownload",
        "application/x-executable",
        "application/x-sh",
        "application/x-bat",
    ];

    if (dangerousMimeTypes.includes(mimeType)) {
        throw new Error("File type not allowed for security reasons");
    }

    if (fileSize > maxSize) {
        throw new Error(`File size exceeds maximum of ${maxSize / (1024 * 1024)}MB`);
    }

    return true;
}
