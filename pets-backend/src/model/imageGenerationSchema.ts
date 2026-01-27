import { Schema, Document, model } from 'mongoose';

export interface IImageGeneration extends Document {
    userId: string;
    prompt: string;
    inputImageLink?: string;
    inputImageBuffer?: Buffer;
    inputImageMimeType?: string;
    outputImageLink?: string;
    outputVideoUrl?: string;
    jobId?: string;
    status: string;
    createdAt: Date;
}

const imageGenerationSchema: Schema = new Schema<IImageGeneration>(
    {
        userId: { type: String, required: true },
        prompt: { type: String, required: true },
        inputImageLink: { type: String },
        inputImageBuffer: { type: Buffer },
        inputImageMimeType: { type: String },
        outputImageLink: { type: String },
        outputVideoUrl: { type: String },
        jobId: { type: String },
        status: { type: String, default: 'pending' },
    },
    { timestamps: true }
);

export const ImageGeneration = model<IImageGeneration>('ImageGeneration', imageGenerationSchema);
