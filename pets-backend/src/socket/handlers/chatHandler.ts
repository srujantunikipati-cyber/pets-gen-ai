import { Server, Socket } from "socket.io";
import { ChatService } from "../../service/chat.service";
import { MessageType } from "../../entities/MessageMetadata";
import { logger } from "../../utils/logger";
import { AuthenticatedSocket } from "../middleware/authMiddleware";

const chatService = new ChatService();

/**
 * Register chat event handlers
 * @param io - Socket.io server instance
 * @param socket - Socket instance
 */
export function registerChatHandlers(io: Server, socket: AuthenticatedSocket): void {
    const userId = socket.userId!;

    // Join user's personal room for receiving messages
    socket.join(userId);
    logger.info(`User ${userId} joined their personal room`);

    // Handle send message
    socket.on("send_message", async (data, callback) => {
        try {
            const {
                receiverId,
                messageType,
                content,
                mediaUrl,
                mediaType,
                mediaSize,
                fileName,
                thumbnailUrl,
                replyToMessageId,
            } = data;

            // Validate required fields
            if (!receiverId || !messageType) {
                return callback({
                    success: false,
                    error: "receiverId and messageType are required",
                });
            }

            // Send message
            const message = await chatService.sendMessage({
                senderId: userId,
                receiverId,
                messageType: messageType as MessageType,
                content,
                mediaUrl,
                mediaType,
                mediaSize,
                fileName,
                thumbnailUrl,
                replyToMessageId,
            });

            // Emit to sender (acknowledgment)
            callback({
                success: true,
                message,
            });

            // Emit to receiver if online
            io.to(receiverId).emit("new_message", message);

            logger.info(`✅ Message sent from ${userId} to ${receiverId}`);
        } catch (error: any) {
            logger.error(`❌ Error sending message: ${error.message}`);
            callback({
                success: false,
                error: error.message || "Failed to send message",
            });
        }
    });

    // Handle message delivered
    socket.on("message_delivered", async (data) => {
        try {
            const { messageId, senderId } = data;

            if (!messageId) {
                return;
            }

            // Mark as delivered
            await chatService.markMessageAsDelivered(messageId);

            // Emit delivery receipt to sender
            io.to(senderId).emit("message_delivered", {
                messageId,
                deliveredAt: new Date(),
            });

            logger.debug(`Message ${messageId} delivered`);
        } catch (error: any) {
            logger.error(`❌ Error marking message as delivered: ${error.message}`);
        }
    });

    // Handle messages read
    socket.on("messages_read", async (data, callback) => {
        try {
            const { messageIds, senderId } = data;

            if (!messageIds || !Array.isArray(messageIds)) {
                return callback({
                    success: false,
                    error: "messageIds array is required",
                });
            }

            // Mark messages as read
            await chatService.markMessagesAsRead(messageIds, userId);

            // Emit read receipts to sender
            io.to(senderId).emit("messages_read", {
                messageIds,
                readAt: new Date(),
                readBy: userId,
            });

            callback({ success: true });

            logger.debug(`${messageIds.length} messages marked as read by ${userId}`);
        } catch (error: any) {
            logger.error(`❌ Error marking messages as read: ${error.message}`);
            callback({
                success: false,
                error: error.message || "Failed to mark messages as read",
            });
        }
    });

    // Handle fetch messages
    socket.on("fetch_messages", async (data, callback) => {
        try {
            const { conversationId, page = 1, limit = 50 } = data;

            if (!conversationId) {
                return callback({
                    success: false,
                    error: "conversationId is required",
                });
            }

            const result = await chatService.getConversationHistory(
                conversationId,
                page,
                limit
            );

            callback({
                success: true,
                data: result,
            });
        } catch (error: any) {
            logger.error(`❌ Error fetching messages: ${error.message}`);
            callback({
                success: false,
                error: error.message || "Failed to fetch messages",
            });
        }
    });

    // Handle fetch conversations
    socket.on("fetch_conversations", async (data, callback) => {
        try {
            const { page = 1, limit = 20 } = data || {};

            const result = await chatService.getUserConversations(userId, page, limit);

            callback({
                success: true,
                data: result,
            });
        } catch (error: any) {
            logger.error(`❌ Error fetching conversations: ${error.message}`);
            callback({
                success: false,
                error: error.message || "Failed to fetch conversations",
            });
        }
    });

    // Handle delete message
    socket.on("delete_message", async (data, callback) => {
        try {
            const { messageId } = data;

            if (!messageId) {
                return callback({
                    success: false,
                    error: "messageId is required",
                });
            }

            await chatService.deleteMessage(messageId, userId);

            callback({ success: true });

            logger.info(`Message ${messageId} deleted by ${userId}`);
        } catch (error: any) {
            logger.error(`❌ Error deleting message: ${error.message}`);
            callback({
                success: false,
                error: error.message || "Failed to delete message",
            });
        }
    });

    // Handle get unread count
    socket.on("get_unread_count", async (callback) => {
        try {
            const count = await chatService.getUnreadCount(userId);

            callback({
                success: true,
                unreadCount: count,
            });
        } catch (error: any) {
            logger.error(`❌ Error getting unread count: ${error.message}`);
            callback({
                success: false,
                error: error.message || "Failed to get unread count",
            });
        }
    });
}
