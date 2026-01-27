import { Schema, Document, model } from 'mongoose';

export interface ILike extends Document {
    userId: string;
    postId: string;
    createdAt: Date;
}

const likeSchema = new Schema<ILike>(
    {
        userId: { type: String, required: true },
        postId: { type: String, required: true, ref: 'Post' }
    },
    { timestamps: true }
);

// Compound index to prevent multiple likes from same user on same post
likeSchema.index({ userId: 1, postId: 1 }, { unique: true });

export const Like = model<ILike>('Like', likeSchema);
