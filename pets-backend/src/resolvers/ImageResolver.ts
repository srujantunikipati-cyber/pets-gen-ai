import { Resolver, Mutation, Query, Arg } from "type-graphql";
import { GraphQLUpload, FileUpload } from "./types/UploadScalar";
import { ImageGenerationService } from "../service/imageGeneration.service";
import { ImageGenerationResponse } from "./dto/imageResolverDto";
import ApiResponse from "../utils/response";
import { logger } from "../utils/logger";

@Resolver()
export class ImageResolver {
    private imageService = new ImageGenerationService();

    @Mutation(() => ImageGenerationResponse)
    async generateImage(
        @Arg("userId") userId: string,
        @Arg("prompt") prompt: string,
        @Arg("image", () => GraphQLUpload) { createReadStream, filename, mimetype }: FileUpload
    ): Promise<ImageGenerationResponse> {
        logger.info(`📸 GraphQL Mutation: generateImage for userId: ${userId}`);

        try {
            // 1. Convert stream to Buffer
            const chunks: Buffer[] = [];
            const stream = createReadStream();

            const buffer = await new Promise<Buffer>((resolve, reject) => {
                stream.on("data", (chunk: any) => chunks.push(Buffer.from(chunk)));
                stream.on("error", (err: any) => reject(err));
                stream.on("end", () => resolve(Buffer.concat(chunks)));
            });

            // 2. Call Service
            const result = await this.imageService.generateImage(
                userId,
                prompt,
                buffer,
                filename,
                mimetype
            );

            return ApiResponse.success({
                jobId: result.jobId,
                status: result.status,
                inputImageUrl: result.inputImageUrl
            }, "Video generation job initiated successfully");

        } catch (error: any) {
            logger.error(`❌ GraphQL generateImage error: ${error.message}`);
            return ApiResponse.error(error.message || "Internal Server Error", 500);
        }
    }

    @Query(() => ImageGenerationResponse)
    async checkVideoStatus(@Arg("jobId") jobId: string): Promise<ImageGenerationResponse> {
        try {
            const result = await this.imageService.getJobStatus(jobId);

            return ApiResponse.success({
                jobId: result.job_id,
                status: result.status,
                videoUrl: result.video_url
            }, "Video status retrieved successfully");
        } catch (error: any) {
            logger.error(`❌ GraphQL checkVideoStatus error: ${error.message}`);
            return ApiResponse.error(error.message || "Internal Server Error", 500);
        }
    }
}
