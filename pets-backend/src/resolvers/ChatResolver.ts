import { Resolver, Query, Mutation, Arg, Int } from "type-graphql";
import { ChatService } from "../service/chat.service";
import {
    PaginatedConversations,
    PaginatedMessages,
    UnreadCountResponse,
    ChatConversation,
    SendMessageInput,
    ChatMessage
} from "./dto/chatDto";
import { logger } from "../utils/logger";
import { emitToUser } from "../socket/server";
import { MessageType } from "../entities/MessageMetadata";

@Resolver()
export class ChatResolver {
    private chatService = new ChatService();

    @Mutation(() => ChatMessage)
    async sendMessage(
        @Arg("input") input: SendMessageInput,
        @Arg("userId") userId: string
    ): Promise<ChatMessage> {
        try {
            const message = await this.chatService.sendMessage({
                ...input,
                senderId: userId,
                messageType: input.messageType as MessageType,
            });

            // Real-time: Emit to receiver
            emitToUser(input.receiverId, "new_message", message);

            return message as unknown as ChatMessage;
        } catch (error: any) {
            logger.error(`Error sending message: ${error.message}`);
            throw new Error(error.message);
        }
    }

    @Query(() => PaginatedConversations)
    async getUserConversations(
        @Arg("userId") userId: string,
        @Arg("page", () => Int, { defaultValue: 1 }) page: number,
        @Arg("limit", () => Int, { defaultValue: 20 }) limit: number
    ): Promise<PaginatedConversations> {
        return this.chatService.getUserConversations(userId, page, limit);
    }

    @Query(() => PaginatedMessages)
    async getConversationMessages(
        @Arg("conversationId") conversationId: string,
        @Arg("page", () => Int, { defaultValue: 1 }) page: number,
        @Arg("limit", () => Int, { defaultValue: 50 }) limit: number
    ): Promise<PaginatedMessages> {
        return this.chatService.getConversationHistory(conversationId, page, limit);
    }

    @Query(() => UnreadCountResponse)
    async getUnreadCount(@Arg("userId") userId: string): Promise<UnreadCountResponse> {
        const count = await this.chatService.getUnreadCount(userId);
        return { unreadCount: count };
    }

    @Mutation(() => Boolean)
    async markMessagesAsRead(
        @Arg("messageIds", () => [String]) messageIds: string[],
        @Arg("userId") userId: string
    ): Promise<boolean> {
        try {
            await this.chatService.markMessagesAsRead(messageIds, userId);
            return true;
        } catch (error: any) {
            logger.error(`Error marking messages as read: ${error.message}`);
            return false;
        }
    }

    @Mutation(() => Boolean)
    async deleteMessage(
        @Arg("messageId") messageId: string,
        @Arg("userId") userId: string
    ): Promise<boolean> {
        try {
            await this.chatService.deleteMessage(messageId, userId);
            return true;
        } catch (error: any) {
            logger.error(`Error deleting message: ${error.message}`);
            return false;
        }
    }

    @Mutation(() => Boolean)
    async blockConversation(
        @Arg("conversationId") conversationId: string,
        @Arg("userId") userId: string
    ): Promise<boolean> {
        try {
            await this.chatService.blockConversation(conversationId, userId);
            return true;
        } catch (error: any) {
            logger.error(`Error blocking conversation: ${error.message}`);
            return false;
        }
    }

    @Mutation(() => Boolean)
    async unblockConversation(
        @Arg("conversationId") conversationId: string
    ): Promise<boolean> {
        try {
            await this.chatService.unblockConversation(conversationId);
            return true;
        } catch (error: any) {
            logger.error(`Error unblocking conversation: ${error.message}`);
            return false;
        }
    }
}
