import { Socket } from "socket.io";
import { logger } from "../../utils/logger";
import admin from "firebase-admin";

export interface AuthenticatedSocket extends Socket {
    userId?: string;
}

/**
 * Middleware to authenticate Socket.io connections using Firebase JWT
 * @param socket - Socket.io socket
 * @param next - Next function
 */
export async function authMiddleware(socket: AuthenticatedSocket, next: Function) {
    try {
        const token = socket.handshake.auth.token || socket.handshake.headers.authorization;

        if (!token) {
            logger.warn(`❌ Socket connection rejected: No token provided`);
            return next(new Error("Authentication error: No token provided"));
        }

        // Remove 'Bearer ' prefix if present
        const cleanToken = token.replace("Bearer ", "");

        // Verify Firebase token
        const decodedToken = await admin.auth().verifyIdToken(cleanToken);

        // Attach user ID to socket
        socket.userId = decodedToken.uid;

        logger.info(`✅ Socket authenticated for user: ${socket.userId}`);
        next();
    } catch (error: any) {
        logger.error(`❌ Socket authentication error: ${error.message}`);
        next(new Error("Authentication error: Invalid token"));
    }
}
