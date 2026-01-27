import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";
import { logger } from "./logger";

const r2Endpoint = process.env.CLOUDFLARE_R2_ENDPOINT || "";
const r2AccessKeyId = process.env.CLOUDFLARE_R2_ACCESS_KEY_ID || "";
const r2SecretAccessKey = process.env.CLOUDFLARE_R2_SECRET_ACCESS_KEY || "";
const r2BucketName = process.env.CLOUDFLARE_R2_BUCKET_NAME || "";

const s3Client = new S3Client({
    region: "auto",
    endpoint: r2Endpoint,
    credentials: {
        accessKeyId: r2AccessKeyId,
        secretAccessKey: r2SecretAccessKey,
    },
});

export const uploadToR2 = async (
    buffer: Buffer,
    fileName: string,
    mimeType: string
): Promise<string> => {
    if (!r2BucketName) {
        throw new Error("CLOUDFLARE_R2_BUCKET_NAME is not defined");
    }

    const key = `uploads/${Date.now()}_${fileName.replace(/\s+/g, '_')}`;

    try {
        const command = new PutObjectCommand({
            Bucket: r2BucketName,
            Key: key,
            Body: buffer,
            ContentType: mimeType,
        });

        await s3Client.send(command);

        // Construct the public URL for R2
        // Note: For R2, the public URL is usually via a custom domain or a specific R2 dev domain.
        // If the user hasn't provided a public domain, we might need to use the R2 endpoint or another variable.
        // Usually, R2 public access is via https://<pub-domain>/<key>
        const publicDomain = process.env.CLOUDFLARE_R2_PUBLIC_DOMAIN;
        const url = publicDomain
            ? `${publicDomain}/${key}`
            : `${r2Endpoint}/${r2BucketName}/${key}`;

        logger.info(`✅ File uploaded to R2: ${url}`);
        return url;
    } catch (error: any) {
        logger.error(`❌ R2 Upload Error: ${error.message}`);
        throw error;
    }
};

export const uploadToS3 = uploadToR2; // Keep backward compatibility if needed
