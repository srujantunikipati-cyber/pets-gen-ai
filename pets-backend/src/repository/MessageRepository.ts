import { AppDataSource } from "../config/postgres";
import { MessageMetadata, MessageType } from "../entities/MessageMetadata";
import { Message, IMessage } from "../model/messageSchema";
import { logger } from "../utils/logger";

export interface CreateMessageData {
    conversationId: string;
    senderId: string;
    receiverId: string;
    messageType: MessageType;
    encryptedContent?: string;
    mediaUrl?: string;
    mediaType?: string;
    mediaSize?: number;
    fileName?: string;
    thumbnailUrl?: string;
    replyToMessageId?: string;
}

export class MessageRepository {
    private metadataRepository = AppDataSource.getRepository(MessageMetadata);

    /**
     * Create a new message (both MongoDB and PostgreSQL)
     * @param data - Message data
     * @returns Created message with metadata
     */
    async createMessage(data: CreateMessageData): Promise<{ message: IMessage; metadata: MessageMetadata }> {
        try {
            // Create MongoDB message
            const mongoMessage = new Message({
                conversationId: data.conversationId,
                senderId: data.senderId,
                receiverId: data.receiverId,
                messageType: data.messageType,
                encryptedContent: data.encryptedContent,
                mediaUrl: data.mediaUrl,
                mediaType: data.mediaType,
                mediaSize: data.mediaSize,
                fileName: data.fileName,
                thumbnailUrl: data.thumbnailUrl,
                replyToMessageId: data.replyToMessageId,
            });

            const savedMessage = await mongoMessage.save();

            // Create PostgreSQL metadata
            const metadata = this.metadataRepository.create({
                conversationId: data.conversationId,
                mongoMessageId: savedMessage._id.toString(),
                senderId: data.senderId,
                receiverId: data.receiverId,
                messageType: data.messageType,
            });

            const savedMetadata = await this.metadataRepository.save(metadata);

            logger.info(`✅ Message created: ${savedMetadata.id}`);

            return { message: savedMessage, metadata: savedMetadata };
        } catch (error: any) {
            logger.error(`❌ Error creating message: ${error.message}`);
            throw error;
        }
    }

    /**
     * Get messages by conversation with pagination
     * @param conversationId - Conversation ID
     * @param page - Page number (default: 1)
     * @param limit - Items per page (default: 50)
     * @returns Messages with metadata
     */
    async getMessagesByConversation(
        conversationId: string,
        page: number = 1,
        limit: number = 50
    ): Promise<{ messages: Array<{ message: IMessage; metadata: MessageMetadata }>; total: number }> {
        try {
            const skip = (page - 1) * limit;

            // Get metadata from PostgreSQL
            const [metadataList, total] = await this.metadataRepository.findAndCount({
                where: { conversationId, isDeleted: false },
                order: { createdAt: "DESC" },
                skip,
                take: limit,
            });

            // Get corresponding messages from MongoDB
            const mongoMessageIds = metadataList.map((m) => m.mongoMessageId);
            const mongoMessages = await Message.find({ _id: { $in: mongoMessageIds } });

            // Map messages to metadata
            const messagesWithMetadata = metadataList.map((metadata) => {
                const message = mongoMessages.find((m) => m._id.toString() === metadata.mongoMessageId);
                return { message: message!, metadata };
            }).filter((item) => item.message); // Filter out any missing messages

            return { messages: messagesWithMetadata, total };
        } catch (error: any) {
            logger.error(`❌ Error getting messages: ${error.message}`);
            throw error;
        }
    }

    /**
     * Mark message as delivered
     * @param messageId - Message metadata ID
     */
    async markAsDelivered(messageId: string): Promise<void> {
        try {
            await this.metadataRepository.update(messageId, {
                isDelivered: true,
                deliveredAt: new Date(),
            });
        } catch (error: any) {
            logger.error(`❌ Error marking message as delivered: ${error.message}`);
            throw error;
        }
    }

    /**
     * Mark messages as read
     * @param messageIds - Array of message metadata IDs
     */
    async markAsRead(messageIds: string[]): Promise<void> {
        try {
            await this.metadataRepository.update(messageIds, {
                isRead: true,
                readAt: new Date(),
            });
            logger.info(`✅ Marked ${messageIds.length} messages as read`);
        } catch (error: any) {
            logger.error(`❌ Error marking messages as read: ${error.message}`);
            throw error;
        }
    }

    /**
     * Delete a message (soft delete)
     * @param messageId - Message metadata ID
     * @param userId - User requesting deletion
     */
    async deleteMessage(messageId: string, userId: string): Promise<void> {
        try {
            const metadata = await this.metadataRepository.findOne({ where: { id: messageId } });

            if (!metadata) {
                throw new Error("Message not found");
            }

            // Only sender can delete their message
            if (metadata.senderId !== userId) {
                throw new Error("Unauthorized to delete this message");
            }

            await this.metadataRepository.update(messageId, {
                isDeleted: true,
            });

            logger.info(`✅ Message ${messageId} deleted by ${userId}`);
        } catch (error: any) {
            logger.error(`❌ Error deleting message: ${error.message}`);
            throw error;
        }
    }

    /**
     * Get unread message count for a user
     * @param userId - User ID
     * @param conversationId - Optional conversation ID to filter by
     * @returns Unread count
     */
    async getUnreadCount(userId: string, conversationId?: string): Promise<number> {
        try {
            const where: any = {
                receiverId: userId,
                isRead: false,
                isDeleted: false,
            };

            if (conversationId) {
                where.conversationId = conversationId;
            }

            return await this.metadataRepository.count({ where });
        } catch (error: any) {
            logger.error(`❌ Error getting unread count: ${error.message}`);
            return 0;
        }
    }

    /**
     * Get unread messages for a user in a conversation
     * @param userId - User ID
     * @param conversationId - Conversation ID
     * @returns Array of unread message IDs
     */
    async getUnreadMessages(userId: string, conversationId: string): Promise<string[]> {
        try {
            const unreadMetadata = await this.metadataRepository.find({
                where: {
                    receiverId: userId,
                    conversationId,
                    isRead: false,
                    isDeleted: false,
                },
                select: ["id"],
            });

            return unreadMetadata.map((m) => m.id);
        } catch (error: any) {
            logger.error(`❌ Error getting unread messages: ${error.message}`);
            return [];
        }
    }
}
