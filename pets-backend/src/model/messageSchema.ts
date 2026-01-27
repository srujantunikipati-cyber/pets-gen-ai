import { Schema, model, Document } from "mongoose";

export interface IMessage extends Document {
    _id: string;
    conversationId: string;
    senderId: string;
    receiverId: string;
    messageType: "text" | "image" | "video" | "file";

    // Content (encrypted for text messages)
    encryptedContent?: string;

    // Media metadata
    mediaUrl?: string;
    mediaType?: string;
    mediaSize?: number;
    fileName?: string;
    thumbnailUrl?: string;

    // Reply/Thread support
    replyToMessageId?: string;

    createdAt: Date;
    updatedAt: Date;
}

const MessageSchema = new Schema<IMessage>(
    {
        conversationId: { type: String, required: true, index: true },
        senderId: { type: String, required: true, index: true },
        receiverId: { type: String, required: true },
        messageType: {
            type: String,
            enum: ["text", "image", "video", "file"],
            required: true,
        },
        encryptedContent: { type: String },
        mediaUrl: { type: String },
        mediaType: { type: String },
        mediaSize: { type: Number },
        fileName: { type: String },
        thumbnailUrl: { type: String },
        replyToMessageId: { type: String },
    },
    {
        timestamps: true,
        collection: "messages",
    }
);

// Compound index for efficient querying
MessageSchema.index({ conversationId: 1, createdAt: -1 });
MessageSchema.index({ senderId: 1, createdAt: -1 });

export const Message = model<IMessage>("Message", MessageSchema);
