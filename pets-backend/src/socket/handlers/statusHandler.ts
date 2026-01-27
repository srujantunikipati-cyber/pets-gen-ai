import { Server, Socket } from "socket.io";
import { redisClient } from "../../config/redis";
import { logger } from "../../utils/logger";
import { AuthenticatedSocket } from "../middleware/authMiddleware";

const USER_STATUS_PREFIX = "user:status:";
const USER_STATUS_TTL = 300; // 5 minutes

export interface UserStatus {
    online: boolean;
    lastSeen: number;
    socketId: string;
}

/**
 * Set user online status
 * @param userId - User ID
 * @param socketId - Socket ID
 */
export async function setUserOnline(userId: string, socketId: string): Promise<void> {
    try {
        const status: UserStatus = {
            online: true,
            lastSeen: Date.now(),
            socketId,
        };

        await redisClient.setex(
            `${USER_STATUS_PREFIX}${userId}`,
            USER_STATUS_TTL,
            JSON.stringify(status)
        );

        logger.info(`✅ User ${userId} is now online`);
    } catch (error: any) {
        logger.error(`❌ Error setting user online: ${error.message}`);
    }
}

/**
 * Set user offline status
 * @param userId - User ID
 */
export async function setUserOffline(userId: string): Promise<void> {
    try {
        const status: UserStatus = {
            online: false,
            lastSeen: Date.now(),
            socketId: "",
        };

        await redisClient.setex(
            `${USER_STATUS_PREFIX}${userId}`,
            USER_STATUS_TTL,
            JSON.stringify(status)
        );

        logger.info(`✅ User ${userId} is now offline`);
    } catch (error: any) {
        logger.error(`❌ Error setting user offline: ${error.message}`);
    }
}

/**
 * Get user status
 * @param userId - User ID
 * @returns User status or null
 */
export async function getUserStatus(userId: string): Promise<UserStatus | null> {
    try {
        const statusStr = await redisClient.get(`${USER_STATUS_PREFIX}${userId}`);

        if (!statusStr) {
            return null;
        }

        return JSON.parse(statusStr);
    } catch (error: any) {
        logger.error(`❌ Error getting user status: ${error.message}`);
        return null;
    }
}

/**
 * Refresh user online status (extend TTL)
 * @param userId - User ID
 */
export async function refreshUserStatus(userId: string): Promise<void> {
    try {
        const status = await getUserStatus(userId);

        if (status && status.online) {
            status.lastSeen = Date.now();
            await redisClient.setex(
                `${USER_STATUS_PREFIX}${userId}`,
                USER_STATUS_TTL,
                JSON.stringify(status)
            );
        }
    } catch (error: any) {
        logger.error(`❌ Error refreshing user status: ${error.message}`);
    }
}

/**
 * Register status event handlers
 * @param io - Socket.io server instance
 * @param socket - Socket instance
 */
export function registerStatusHandlers(io: Server, socket: AuthenticatedSocket): void {
    const userId = socket.userId!;

    // Set user online when connected
    setUserOnline(userId, socket.id);

    // Emit online status to user's contacts (you can customize this logic)
    socket.broadcast.emit("user_online", { userId, timestamp: Date.now() });

    // Handle get user status request
    socket.on("get_user_status", async (data: { userId: string }, callback) => {
        try {
            const status = await getUserStatus(data.userId);
            callback({ success: true, status });
        } catch (error: any) {
            callback({ success: false, error: error.message });
        }
    });

    // Handle get multiple users status
    socket.on("get_users_status", async (data: { userIds: string[] }, callback) => {
        try {
            const statuses = await Promise.all(
                data.userIds.map(async (uid) => ({
                    userId: uid,
                    status: await getUserStatus(uid),
                }))
            );
            callback({ success: true, statuses });
        } catch (error: any) {
            callback({ success: false, error: error.message });
        }
    });

    // Refresh status periodically (client should send this every minute)
    socket.on("refresh_status", async () => {
        await refreshUserStatus(userId);
    });

    // Handle disconnect
    socket.on("disconnect", async () => {
        await setUserOffline(userId);
        socket.broadcast.emit("user_offline", { userId, timestamp: Date.now() });
        logger.info(`User ${userId} disconnected`);
    });
}
