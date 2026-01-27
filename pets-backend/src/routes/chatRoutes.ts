import { Router, Request, Response } from "express";
import { ChatService } from "../service/chat.service";
import { logger } from "../utils/logger";

const router = Router();
const chatService = new ChatService();

/**
 * GET /api/chat/conversations
 * Get user's conversations
 */
router.get("/conversations", async (req: Request, res: Response) => {
    try {
        const userId = req.query.userId as string;
        const page = parseInt(req.query.page as string) || 1;
        const limit = parseInt(req.query.limit as string) || 20;

        if (!userId) {
            return res.status(400).json({ error: "userId is required" });
        }

        const result = await chatService.getUserConversations(userId, page, limit);

        res.json({
            success: true,
            data: result,
        });
    } catch (error: any) {
        logger.error(`❌ Get conversations error: ${error.message}`);
        res.status(500).json({ error: error.message || "Failed to get conversations" });
    }
});

/**
 * GET /api/chat/conversations/:conversationId/messages
 * Get conversation messages
 */
router.get("/conversations/:conversationId/messages", async (req: Request, res: Response) => {
    try {
        const { conversationId } = req.params;
        const page = parseInt(req.query.page as string) || 1;
        const limit = parseInt(req.query.limit as string) || 50;

        const result = await chatService.getConversationHistory(conversationId, page, limit);

        res.json({
            success: true,
            data: result,
        });
    } catch (error: any) {
        logger.error(`❌ Get messages error: ${error.message}`);
        res.status(500).json({ error: error.message || "Failed to get messages" });
    }
});

/**
 * POST /api/chat/messages/:messageId/read
 * Mark messages as read
 */
router.post("/messages/read", async (req: Request, res: Response) => {
    try {
        const { messageIds, userId } = req.body;

        if (!messageIds || !Array.isArray(messageIds) || messageIds.length === 0) {
            return res.status(400).json({ error: "messageIds array is required" });
        }

        if (!userId) {
            return res.status(400).json({ error: "userId is required" });
        }

        await chatService.markMessagesAsRead(messageIds, userId);

        res.json({
            success: true,
            message: "Messages marked as read",
        });
    } catch (error: any) {
        logger.error(`❌ Mark as read error: ${error.message}`);
        res.status(500).json({ error: error.message || "Failed to mark messages as read" });
    }
});

/**
 * DELETE /api/chat/messages/:messageId
 * Delete a message
 */
router.delete("/messages/:messageId", async (req: Request, res: Response) => {
    try {
        const { messageId } = req.params;
        const userId = req.query.userId as string;

        if (!userId) {
            return res.status(400).json({ error: "userId is required" });
        }

        await chatService.deleteMessage(messageId, userId);

        res.json({
            success: true,
            message: "Message deleted",
        });
    } catch (error: any) {
        logger.error(`❌ Delete message error: ${error.message}`);
        res.status(500).json({ error: error.message || "Failed to delete message" });
    }
});

/**
 * GET /api/chat/unread-count
 * Get unread message count
 */
router.get("/unread-count", async (req: Request, res: Response) => {
    try {
        const userId = req.query.userId as string;

        if (!userId) {
            return res.status(400).json({ error: "userId is required" });
        }

        const count = await chatService.getUnreadCount(userId);

        res.json({
            success: true,
            data: { unreadCount: count },
        });
    } catch (error: any) {
        logger.error(`❌ Get unread count error: ${error.message}`);
        res.status(500).json({ error: error.message || "Failed to get unread count" });
    }
});

/**
 * POST /api/chat/conversations/:conversationId/block
 * Block a conversation
 */
router.post("/conversations/:conversationId/block", async (req: Request, res: Response) => {
    try {
        const { conversationId } = req.params;
        const { userId } = req.body;

        if (!userId) {
            return res.status(400).json({ error: "userId is required" });
        }

        await chatService.blockConversation(conversationId, userId);

        res.json({
            success: true,
            message: "Conversation blocked",
        });
    } catch (error: any) {
        logger.error(`❌ Block conversation error: ${error.message}`);
        res.status(500).json({ error: error.message || "Failed to block conversation" });
    }
});

/**
 * POST /api/chat/conversations/:conversationId/unblock
 * Unblock a conversation
 */
router.post("/conversations/:conversationId/unblock", async (req: Request, res: Response) => {
    try {
        const { conversationId } = req.params;

        await chatService.unblockConversation(conversationId);

        res.json({
            success: true,
            message: "Conversation unblocked",
        });
    } catch (error: any) {
        logger.error(`❌ Unblock conversation error: ${error.message}`);
        res.status(500).json({ error: error.message || "Failed to unblock conversation" });
    }
});

export default router;
