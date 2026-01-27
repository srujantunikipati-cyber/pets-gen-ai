import { Schema, Document, model } from 'mongoose';

export interface IPost extends Document {
    userId: string; // The user who created the post
    contentUrl: string; // URL of the video or image
    caption?: string;
    type: 'video' | 'image';
    stats: {
        likeCount: number;
        commentCount: number;
        shareCount: number;
    };
    createdAt: Date;
    updatedAt: Date;
}

const postSchema = new Schema<IPost>(
    {
        userId: { type: String, required: true, index: true },
        contentUrl: { type: String, required: true },
        caption: { type: String },
        type: { type: String, enum: ['video', 'image'], required: true },
        stats: {
            likeCount: { type: Number, default: 0 },
            commentCount: { type: Number, default: 0 },
            shareCount: { type: Number, default: 0 }
        }
    },
    { timestamps: true }
);

export const Post = model<IPost>('Post', postSchema);
