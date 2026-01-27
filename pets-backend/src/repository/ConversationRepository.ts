import { AppDataSource } from "../config/postgres";
import { Conversation } from "../entities/Conversation";
import { logger } from "../utils/logger";

export class ConversationRepository {
    private repository = AppDataSource.getRepository(Conversation);

    /**
     * Find or create a conversation between two users
     * @param user1Id - First user ID
     * @param user2Id - Second user ID
     * @returns Conversation entity
     */
    async findOrCreateConversation(user1Id: string, user2Id: string): Promise<Conversation> {
        try {
            // Ensure consistent ordering to avoid duplicate conversations
            const [participantA, participantB] = [user1Id, user2Id].sort();

            let conversation = await this.repository.findOne({
                where: [
                    { participant1Id: participantA, participant2Id: participantB },
                    { participant1Id: participantB, participant2Id: participantA },
                ],
            });

            if (!conversation) {
                conversation = this.repository.create({
                    participant1Id: participantA,
                    participant2Id: participantB,
                });
                await this.repository.save(conversation);
                logger.info(`✅ Created new conversation: ${conversation.id}`);
            }

            return conversation;
        } catch (error: any) {
            logger.error(`❌ Error finding/creating conversation: ${error.message}`);
            throw error;
        }
    }

    /**
     * Get conversation by ID
     * @param conversationId - Conversation ID
     * @returns Conversation entity or null
     */
    async getConversationById(conversationId: string): Promise<Conversation | null> {
        try {
            return await this.repository.findOne({ where: { id: conversationId } });
        } catch (error: any) {
            logger.error(`❌ Error getting conversation: ${error.message}`);
            throw error;
        }
    }

    /**
     * Get all conversations for a user
     * @param userId - User ID
     * @param page - Page number (default: 1)
     * @param limit - Items per page (default: 20)
     * @returns Array of conversations
     */
    async getUserConversations(
        userId: string,
        page: number = 1,
        limit: number = 20
    ): Promise<{ conversations: Conversation[]; total: number }> {
        try {
            const skip = (page - 1) * limit;

            const [conversations, total] = await this.repository.findAndCount({
                where: [
                    { participant1Id: userId },
                    { participant2Id: userId },
                ],
                order: {
                    lastMessageAt: "DESC",
                },
                skip,
                take: limit,
            });

            return { conversations, total };
        } catch (error: any) {
            logger.error(`❌ Error getting user conversations: ${error.message}`);
            throw error;
        }
    }

    /**
     * Update last message preview and timestamp
     * @param conversationId - Conversation ID
     * @param preview - Message preview text
     * @param timestamp - Message timestamp
     */
    async updateLastMessage(
        conversationId: string,
        preview: string,
        timestamp: Date
    ): Promise<void> {
        try {
            await this.repository.update(conversationId, {
                lastMessagePreview: preview.substring(0, 500), // Limit to 500 chars
                lastMessageAt: timestamp,
            });
        } catch (error: any) {
            logger.error(`❌ Error updating last message: ${error.message}`);
            throw error;
        }
    }

    /**
     * Block a conversation
     * @param conversationId - Conversation ID
     * @param userId - User who is blocking
     */
    async blockConversation(conversationId: string, userId: string): Promise<void> {
        try {
            await this.repository.update(conversationId, {
                isBlocked: true,
                blockedBy: userId,
            });
            logger.info(`✅ Conversation ${conversationId} blocked by ${userId}`);
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
            await this.repository.update(conversationId, {
                isBlocked: false,
                blockedBy: undefined,
            });
            logger.info(`✅ Conversation ${conversationId} unblocked`);
        } catch (error: any) {
            logger.error(`❌ Error unblocking conversation: ${error.message}`);
            throw error;
        }
    }

    /**
     * Check if conversation is blocked
     * @param conversationId - Conversation ID
     * @returns true if blocked, false otherwise
     */
    async isConversationBlocked(conversationId: string): Promise<boolean> {
        try {
            const conversation = await this.repository.findOne({
                where: { id: conversationId },
                select: ["isBlocked"],
            });
            return conversation?.isBlocked || false;
        } catch (error: any) {
            logger.error(`❌ Error checking if conversation is blocked: ${error.message}`);
            return false;
        }
    }
}
