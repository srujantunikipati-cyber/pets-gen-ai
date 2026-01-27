import { ConversationRepository } from "../repository/ConversationRepository";
import { MessageRepository, CreateMessageData } from "../repository/MessageRepository";
import { MessageType } from "../entities/MessageMetadata";
import { encryptMessage, decryptMessage, validateMessageContent, sanitizeMessageContent } from "../utils/encryption";
import { logger } from "../utils/logger";
import { IMessage } from "../model/messageSchema";
import { MessageMetadata } from "../entities/MessageMetadata";

export interface SendMessageParams {
    senderId: string;
    receiverId: string;
    messageType: MessageType;
    content?: string;
    mediaUrl?: string;
    mediaType?: string;
    mediaSize?: number;
    fileName?: string;
    thumbnailUrl?: string;
    replyToMessageId?: string;
}

export interface MessageWithMetadata {
    id: string;
    conversationId: string;
    senderId: string;
    receiverId: string;
    messageType: MessageType;
    content?: string;
    mediaUrl?: string;
    mediaType?: string;
    mediaSize?: number;
    fileName?: string;
    thumbnailUrl?: string;
    replyToMessageId?: string;
    isDelivered: boolean;
    isRead: boolean;
    deliveredAt?: Date;
    readAt?: Date;
    createdAt: Date;
}

export class ChatService {
    private conversationRepo = new ConversationRepository();
    private messageRepo = new MessageRepository();

    /**
     * Send a message
     * @param params - Message parameters
     * @returns Created message with metadata
     */
    async sendMessage(params: SendMessageParams): Promise<MessageWithMetadata> {
        try {
            // Find or create conversation
            const conversation = await this.conversationRepo.findOrCreateConversation(
                params.senderId,
                params.receiverId
            );

            // Check if conversation is blocked
            const isBlocked = await this.conversationRepo.isConversationBlocked(conversation.id);
            if (isBlocked) {
                throw new Error("Cannot send message to blocked conversation");
            }

            // Prepare message data
            const messageData: CreateMessageData = {
                conversationId: conversation.id,
                senderId: params.senderId,
                receiverId: params.receiverId,
                messageType: params.messageType,
                mediaUrl: params.mediaUrl,
                mediaType: params.mediaType,
                mediaSize: params.mediaSize,
                fileName: params.fileName,
                thumbnailUrl: params.thumbnailUrl,
                replyToMessageId: params.replyToMessageId,
            };

            // Encrypt text content if provided
            if (params.content && params.messageType === MessageType.TEXT) {
                validateMessageContent(params.content);
                const sanitized = sanitizeMessageContent(params.content);
                const encrypted = encryptMessage(sanitized);
                messageData.encryptedContent = encrypted.encrypted;
            }

            // Create message
            const { message, metadata } = await this.messageRepo.createMessage(messageData);

            // Update conversation last message
            const preview = this.generateMessagePreview(params);
            await this.conversationRepo.updateLastMessage(
                conversation.id,
                preview,
                metadata.createdAt
            );

            // Return formatted message
            return this.formatMessage(message, metadata);
        } catch (error: any) {
            logger.error(`❌ Error sending message: ${error.message}`);
            throw error;
        }
    }

    /**
     * Get conversation history with decrypted messages
     * @param conversationId - Conversation ID
     * @param page - Page number
     * @param limit - Items per page
     * @returns Messages with metadata
     */
    async getConversationHistory(
        conversationId: string,
        page: number = 1,
        limit: number = 50
    ): Promise<{ messages: MessageWithMetadata[]; total: number }> {
        try {
            const { messages, total } = await this.messageRepo.getMessagesByConversation(
                conversationId,
                page,
                limit
            );

            const formattedMessages = messages.map(({ message, metadata }) =>
                this.formatMessage(message, metadata)
            );

            return { messages: formattedMessages, total };
        } catch (error: any) {
            logger.error(`❌ Error getting conversation history: ${error.message}`);
            throw error;
        }
    }

    /**
     * Get user's conversations
     * @param userId - User ID
     * @param page - Page number
     * @param limit - Items per page
     * @returns Conversations with unread counts
     */
    async getUserConversations(
        userId: string,
        page: number = 1,
        limit: number = 20
    ): Promise<any> {
        try {
            const { conversations, total } = await this.conversationRepo.getUserConversations(
                userId,
                page,
                limit
            );

            // Get unread counts for each conversation
            const conversationsWithUnread = await Promise.all(
                conversations.map(async (conv) => {
                    const unreadCount = await this.messageRepo.getUnreadCount(userId, conv.id);
                    return {
                        id: conv.id,
                        participant1Id: conv.participant1Id,
                        participant2Id: conv.participant2Id,
                        lastMessageAt: conv.lastMessageAt,
                        lastMessagePreview: conv.lastMessagePreview,
                        isBlocked: conv.isBlocked,
                        unreadCount,
                    };
                })
            );

            return { conversations: conversationsWithUnread, total };
        } catch (error: any) {
            logger.error(`❌ Error getting user conversations: ${error.message}`);
            throw error;
        }
    }

    /**
     * Mark messages as read
     * @param messageIds - Array of message IDs
     * @param userId - User ID (for verification)
     */
    async markMessagesAsRead(messageIds: string[], userId: string): Promise<void> {
        try {
            await this.messageRepo.markAsRead(messageIds);
        } catch (error: any) {
            logger.error(`❌ Error marking messages as read: ${error.message}`);
            throw error;
        }
    }

    /**
     * Mark message as delivered
     * @param messageId - Message ID
     */
    async markMessageAsDelivered(messageId: string): Promise<void> {
        try {
            await this.messageRepo.markAsDelivered(messageId);
        } catch (error: any) {
            logger.error(`❌ Error marking message as delivered: ${error.message}`);
            throw error;
        }
    }

    /**
     * Delete a message
     * @param messageId - Message ID
     * @param userId - User ID
     */
    async deleteMessage(messageId: string, userId: string): Promise<void> {
        try {
            await this.messageRepo.deleteMessage(messageId, userId);
        } catch (error: any) {
            logger.error(`❌ Error deleting message: ${error.message}`);
            throw error;
        }
    }

    /**
     * Get unread message count for user
     * @param userId - User ID
     * @returns Unread count
     */
    async getUnreadCount(userId: string): Promise<number> {
        try {
            return await this.messageRepo.getUnreadCount(userId);
        } catch (error: any) {
            logger.error(`❌ Error getting unread count: ${error.message}`);
            return 0;
        }
    }

    /**
     * Block a conversation
     * @param conversationId - Conversation ID
     * @param userId - User ID
     */
    async blockConversation(conversationId: string, userId: string): Promise<void> {
        try {
            await this.conversationRepo.blockConversation(conversationId, userId);
        } catch (error: any) {
            logger.error(`❌ Error blocking conversation: ${error.message}`);
            throw error;
        }
    }

    /**
     * Unblock a conversation
     * @param conversationId - Conversation ID
     */
    async unblockConversation(conversationId: string): Promise<void> {
        try {
            await this.conversationRepo.unblockConversation(conversationId);
        } catch (error: any) {
            logger.error(`❌ Error unblocking conversation: ${error.message}`);
            throw error;
        }
    }

    /**
     * Format message with decrypted content
     * @param message - MongoDB message
     * @param metadata - PostgreSQL metadata
     * @returns Formatted message
     */
    private formatMessage(message: IMessage, metadata: MessageMetadata): MessageWithMetadata {
        let content: string | undefined;

        // Decrypt text content
        if (message.encryptedContent && message.messageType === "text") {
            try {
                content = decryptMessage(message.encryptedContent);
            } catch (error) {
                logger.error(`Failed to decrypt message ${metadata.id}`);
                content = "[Encrypted message]";
            }
        }

        return {
            id: metadata.id,
            conversationId: metadata.conversationId,
            senderId: metadata.senderId,
            receiverId: metadata.receiverId,
            messageType: metadata.messageType,
            content,
            mediaUrl: message.mediaUrl,
            mediaType: message.mediaType,
            mediaSize: message.mediaSize,
            fileName: message.fileName,
            thumbnailUrl: message.thumbnailUrl,
            replyToMessageId: message.replyToMessageId,
            isDelivered: metadata.isDelivered,
            isRead: metadata.isRead,
            deliveredAt: metadata.deliveredAt,
            readAt: metadata.readAt,
            createdAt: metadata.createdAt,
        };
    }

    /**
     * Generate message preview for conversation list
     * @param params - Message parameters
     * @returns Preview text
     */
    private generateMessagePreview(params: SendMessageParams): string {
        switch (params.messageType) {
            case MessageType.TEXT:
                return params.content?.substring(0, 100) || "";
            case MessageType.IMAGE:
                return "📷 Image";
            case MessageType.VIDEO:
                return "🎥 Video";
            case MessageType.FILE:
                return `📎 ${params.fileName || "File"}`;
            default:
                return "Message";
        }
    }
}
