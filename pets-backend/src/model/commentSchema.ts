import { Schema, Document, model } from 'mongoose';

export interface IComment extends Document {
    userId: string;
    postId: string;
    text: string;
    createdAt: Date;
    updatedAt: Date;
}

const commentSchema = new Schema<IComment>(
    {
        userId: { type: String, required: true },
        postId: { type: String, required: true, ref: 'Post', index: true },
        text: { type: String, required: true }
    },
    { timestamps: true }
);

export const Comment = model<IComment>('Comment', commentSchema);
