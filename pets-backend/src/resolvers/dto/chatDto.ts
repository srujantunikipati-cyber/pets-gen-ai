import { ObjectType, Field, ID, Int, InputType } from "type-graphql";

@ObjectType()
export class ChatConversation {
    @Field(() => ID)
    id!: string;

    @Field(() => ID)
    participant1Id!: string;

    @Field(() => ID)
    participant2Id!: string;

    @Field({ nullable: true })
    lastMessageAt?: Date;

    @Field({ nullable: true })
    lastMessagePreview?: string;

    @Field()
    isBlocked!: boolean;

    @Field(() => Int)
    unreadCount!: number;
}

@ObjectType()
export class PaginatedConversations {
    @Field(() => [ChatConversation])
    conversations!: ChatConversation[];

    @Field(() => Int)
    total!: number;
}

@ObjectType()
export class ChatMessage {
    @Field(() => ID)
    id!: string;

    @Field(() => ID)
    conversationId!: string;

    @Field(() => ID)
    senderId!: string;

    @Field(() => ID)
    receiverId!: string;

    @Field()
    messageType!: string;

    @Field({ nullable: true })
    content?: string;

    @Field({ nullable: true })
    mediaUrl?: string;

    @Field({ nullable: true })
    mediaType?: string;

    @Field(() => Int, { nullable: true })
    mediaSize?: number;

    @Field({ nullable: true })
    fileName?: string;

    @Field({ nullable: true })
    thumbnailUrl?: string;

    @Field({ nullable: true })
    replyToMessageId?: string;

    @Field()
    isDelivered!: boolean;

    @Field()
    isRead!: boolean;

    @Field({ nullable: true })
    deliveredAt?: Date;

    @Field({ nullable: true })
    readAt?: Date;

    @Field()
    createdAt!: Date;
}

@ObjectType()
export class PaginatedMessages {
    @Field(() => [ChatMessage])
    messages!: ChatMessage[];

    @Field(() => Int)
    total!: number;
}

@ObjectType()
export class UnreadCountResponse {
    @Field(() => Int)
    unreadCount!: number;
}

@ObjectType()
export class ChatMediaUploadResult {
    @Field()
    url!: string;

    @Field({ nullable: true })
    thumbnailUrl?: string;

    @Field(() => Int)
    size!: number;

    @Field(() => Int, { nullable: true })
    width?: number;

    @Field(() => Int, { nullable: true })
    height?: number;

    @Field({ nullable: true })
    fileName?: string;

    @Field({ nullable: true })
    fileType?: string;
}

@InputType()
export class SendMessageInput {
    @Field(() => ID)
    receiverId!: string;

    @Field()
    messageType!: string;

    @Field({ nullable: true })
    content?: string;

    @Field({ nullable: true })
    mediaUrl?: string;

    @Field({ nullable: true })
    mediaType?: string;

    @Field(() => Int, { nullable: true })
    mediaSize?: number;

    @Field({ nullable: true })
    fileName?: string;

    @Field({ nullable: true })
    thumbnailUrl?: string;

    @Field({ nullable: true })
    replyToMessageId?: string;
}
