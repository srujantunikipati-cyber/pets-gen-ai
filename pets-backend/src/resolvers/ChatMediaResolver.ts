import { Resolver, Mutation, Arg } from "type-graphql";
import { GraphQLUpload, FileUpload } from "./types/UploadScalar";
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
import { ChatMediaUploadResult } from "./dto/chatDto";
import { logger } from "../utils/logger";

@Resolver()
export class ChatMediaResolver {

    private async streamToBuffer(stream: NodeJS.ReadableStream): Promise<Buffer> {
        const chunks: Buffer[] = [];
        return new Promise((resolve, reject) => {
            stream.on("data", (chunk) => chunks.push(Buffer.from(chunk)));
            stream.on("error", (err) => reject(err));
            stream.on("end", () => resolve(Buffer.concat(chunks)));
        });
    }

    @Mutation(() => ChatMediaUploadResult)
    async uploadChatImage(
        @Arg("file", () => GraphQLUpload) { createReadStream, filename, mimetype }: FileUpload,
        @Arg("userId") userId: string,
        @Arg("conversationId") conversationId: string
    ): Promise<ChatMediaUploadResult> {
        try {
            const buffer = await this.streamToBuffer(createReadStream());

            // Validate image (5MB max)
            await validateImage(buffer, 5 * 1024 * 1024);

            // Compress image
            const compressed = await compressImage(buffer);

            // Generate thumbnail
            const thumbnail = await generateImageThumbnail(buffer);

            // Upload to R2
            const result = await uploadImageWithThumbnail(
                compressed.buffer,
                thumbnail.buffer,
                filename,
                compressed.mimeType,
                userId,
                conversationId
            );

            logger.info(`✅ Image uploaded successfully for user ${userId}`);

            return {
                url: result.imageUrl,
                thumbnailUrl: result.thumbnailUrl,
                size: result.imageSize,
                width: compressed.width,
                height: compressed.height,
                fileName: filename,
                fileType: compressed.mimeType
            };
        } catch (error: any) {
            logger.error(`❌ Image upload error: ${error.message}`);
            throw new Error(error.message || "Failed to upload image");
        }
    }

    @Mutation(() => ChatMediaUploadResult)
    async uploadChatVideo(
        @Arg("file", () => GraphQLUpload) { createReadStream, filename, mimetype }: FileUpload,
        @Arg("userId") userId: string,
        @Arg("conversationId") conversationId: string
    ): Promise<ChatMediaUploadResult> {
        try {
            const buffer = await this.streamToBuffer(createReadStream());

            // Validate video (50MB max)
            validateVideo(mimetype, buffer.length, 50 * 1024 * 1024);

            // Upload to R2
            const result = await uploadVideo(
                buffer,
                filename,
                mimetype,
                userId,
                conversationId
            );

            logger.info(`✅ Video uploaded successfully for user ${userId}`);

            return {
                url: result.url,
                size: result.size,
                fileName: filename,
                fileType: mimetype
            };
        } catch (error: any) {
            logger.error(`❌ Video upload error: ${error.message}`);
            throw new Error(error.message || "Failed to upload video");
        }
    }

    @Mutation(() => ChatMediaUploadResult)
    async uploadChatFile(
        @Arg("file", () => GraphQLUpload) { createReadStream, filename, mimetype }: FileUpload,
        @Arg("userId") userId: string,
        @Arg("conversationId") conversationId: string
    ): Promise<ChatMediaUploadResult> {
        try {
            const buffer = await this.streamToBuffer(createReadStream());

            // Validate file (10MB max)
            validateFile(mimetype, buffer.length, 10 * 1024 * 1024);

            // Upload to R2
            const result = await uploadFile(
                buffer,
                filename,
                mimetype,
                userId,
                conversationId
            );

            logger.info(`✅ File uploaded successfully for user ${userId}`);

            return {
                url: result.url,
                size: result.size,
                fileName: filename,
                fileType: mimetype
            };
        } catch (error: any) {
            logger.error(`❌ File upload error: ${error.message}`);
            throw new Error(error.message || "Failed to upload file");
        }
    }
}
