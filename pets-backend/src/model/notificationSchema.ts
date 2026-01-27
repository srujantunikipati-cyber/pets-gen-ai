import { Schema, Document, model } from 'mongoose';

export interface INotification extends Document {
    recipientId: string; // The user receiving the notification (e.g., post author)
    actorId: string; // The user performing the action (liker/commenter)
    type: 'LIKE' | 'COMMENT';
    entityId: string; // The ID of the Post related to the notification
    isRead: boolean;
    createdAt: Date;
}

const notificationSchema = new Schema<INotification>(
    {
        recipientId: { type: String, required: true, index: true },
        actorId: { type: String, required: true },
        type: { type: String, enum: ['LIKE', 'COMMENT'], required: true },
        entityId: { type: String, required: true },
        isRead: { type: Boolean, default: false }
    },
    { timestamps: true }
);

export const Notification = model<INotification>('Notification', notificationSchema);
