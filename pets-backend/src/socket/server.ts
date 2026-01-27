import { Server as HttpServer } from "http";
import { Server, Socket } from "socket.io";
import { authMiddleware, AuthenticatedSocket } from "./middleware/authMiddleware";
import { registerChatHandlers } from "./handlers/chatHandler";
import { registerStatusHandlers } from "./handlers/statusHandler";
import { registerTypingHandlers } from "./handlers/typingHandler";
import { logger } from "../utils/logger";

let io: Server | null = null;

/**
 * Initialize Socket.io server
 * @param httpServer - HTTP server instance
 * @returns Socket.io server instance
 */
export function initializeSocketServer(httpServer: HttpServer): Server {
    const corsOrigin = process.env.SOCKET_CORS_ORIGIN?.split(",") || ["http://localhost:3000"];

    io = new Server(httpServer, {
        cors: {
            origin: corsOrigin,
            methods: ["GET", "POST"],
            credentials: true,
        },
        pingTimeout: 60000,
        pingInterval: 25000,
    });

    // Apply authentication middleware
    io.use(authMiddleware as any);

    // Handle connections
    io.on("connection", (socket: Socket) => {
        const authSocket = socket as AuthenticatedSocket;
        const userId = authSocket.userId;

        logger.info(`✅ Socket connected: ${socket.id} (User: ${userId})`);

        // Register all event handlers
        registerChatHandlers(io!, authSocket);
        registerStatusHandlers(io!, authSocket);
        registerTypingHandlers(io!, authSocket);

        // Handle errors
        socket.on("error", (error) => {
            logger.error(`❌ Socket error for user ${userId}: ${error.message}`);
        });

        // Handle disconnect
        socket.on("disconnect", (reason) => {
            logger.info(`Socket disconnected: ${socket.id} (User: ${userId}) - Reason: ${reason}`);
        });
    });

    logger.info(`✅ Socket.io server initialized with CORS: ${corsOrigin.join(", ")}`);

    return io;
}

/**
 * Get Socket.io server instance
 * @returns Socket.io server instance or null
 */
export function getSocketServer(): Server | null {
    return io;
}

/**
 * Emit event to specific user
 * @param userId - User ID
 * @param event - Event name
 * @param data - Event data
 */
export function emitToUser(userId: string, event: string, data: any): void {
    if (io) {
        io.to(userId).emit(event, data);
    }
}

/**
 * Emit event to multiple users
 * @param userIds - Array of user IDs
 * @param event - Event name
 * @param data - Event data
 */
export function emitToUsers(userIds: string[], event: string, data: any): void {
    if (io) {
        userIds.forEach((userId) => {
            io!.to(userId).emit(event, data);
        });
    }
}

/**
 * Broadcast event to all connected users
 * @param event - Event name
 * @param data - Event data
 */
export function broadcastEvent(event: string, data: any): void {
    if (io) {
        io.emit(event, data);
    }
}

/**
 * Close Socket.io server
 */
export async function closeSocketServer(): Promise<void> {
    if (io) {
        await new Promise<void>((resolve) => {
            io!.close(() => {
                logger.info("Socket.io server closed");
                resolve();
            });
        });
        io = null;
    }
}
