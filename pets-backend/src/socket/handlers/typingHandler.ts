import { Server, Socket } from "socket.io";
import { redisClient } from "../../config/redis";
import { logger } from "../../utils/logger";
import { AuthenticatedSocket } from "../middleware/authMiddleware";

const TYPING_PREFIX = "typing:";
const TYPING_TTL = 5; // 5 seconds

/**
 * Register typing indicator handlers
 * @param io - Socket.io server instance
 * @param socket - Socket instance
 */
export function registerTypingHandlers(io: Server, socket: AuthenticatedSocket): void {
    const userId = socket.userId!;

    // Handle typing start
    socket.on("typing_start", async (data: { conversationId: string; receiverId: string }) => {
        try {
            const { conversationId, receiverId } = data;

            // Set typing indicator in Redis with TTL
            const key = `${TYPING_PREFIX}${conversationId}:${userId}`;
            await redisClient.setex(key, TYPING_TTL, "1");

            // Emit to receiver
            io.to(receiverId).emit("user_typing", {
                conversationId,
                userId,
                timestamp: Date.now(),
            });

            logger.debug(`User ${userId} started typing in conversation ${conversationId}`);
        } catch (error: any) {
            logger.error(`❌ Error handling typing start: ${error.message}`);
        }
    });

    // Handle typing stop
    socket.on("typing_stop", async (data: { conversationId: string; receiverId: string }) => {
        try {
            const { conversationId, receiverId } = data;

            // Remove typing indicator from Redis
            const key = `${TYPING_PREFIX}${conversationId}:${userId}`;
            await redisClient.del(key);

            // Emit to receiver
            io.to(receiverId).emit("user_stopped_typing", {
                conversationId,
                userId,
                timestamp: Date.now(),
            });

            logger.debug(`User ${userId} stopped typing in conversation ${conversationId}`);
        } catch (error: any) {
            logger.error(`❌ Error handling typing stop: ${error.message}`);
        }
    });

    // Check if user is typing in a conversation
    socket.on("check_typing", async (data: { conversationId: string; userId: string }, callback) => {
        try {
            const key = `${TYPING_PREFIX}${data.conversationId}:${data.userId}`;
            const isTyping = await redisClient.exists(key);

            callback({ success: true, isTyping: isTyping === 1 });
        } catch (error: any) {
            callback({ success: false, error: error.message });
        }
    });
}
