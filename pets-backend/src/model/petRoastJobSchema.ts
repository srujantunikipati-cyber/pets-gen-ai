import { Schema, Document, model } from 'mongoose';

export interface IPetRoastJob extends Document {
    userId: string;
    jobId: string;
    prompt: string;
    inputImageUrl?: string;
    inputImageBuffer?: Buffer;
    inputImageMimeType?: string;
    videoUrl?: string;
    status: string;
    createdAt: Date;
    updatedAt: Date;
}

const petRoastJobSchema: Schema = new Schema<IPetRoastJob>(
    {
        userId: { type: String, required: true },
        jobId: { type: String, required: true, unique: true },
        prompt: { type: String, required: true },
        inputImageUrl: { type: String },
        inputImageBuffer: { type: Buffer },
        inputImageMimeType: { type: String },
        videoUrl: { type: String },
        status: { type: String, default: 'pending' },
    },
    { timestamps: true }
);

export const PetRoastJob = model<IPetRoastJob>('PetRoastJob', petRoastJobSchema);
