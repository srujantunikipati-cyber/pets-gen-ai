import {
    Entity,
    PrimaryGeneratedColumn,
    Column,
    CreateDateColumn,
    Index,
} from "typeorm";

export enum MessageType {
    TEXT = "text",
    IMAGE = "image",
    VIDEO = "video",
    FILE = "file",
}

@Entity("message_metadata")
@Index(["conversationId", "createdAt"])
@Index(["receiverId", "isRead"])
export class MessageMetadata {
    @PrimaryGeneratedColumn("uuid")
    id!: string;

    @Column({ type: "uuid" })
    @Index()
    conversationId!: string;

    @Column({ type: "varchar" })
    mongoMessageId!: string; // Reference to MongoDB document

    @Column({ type: "varchar" })
    @Index()
    senderId!: string;

    @Column({ type: "varchar" })
    receiverId!: string;

    @Column({
        type: "enum",
        enum: MessageType,
    })
    messageType!: MessageType;

    @Column({ type: "boolean", default: false })
    isDelivered!: boolean;

    @Column({ type: "boolean", default: false })
    isRead!: boolean;

    @Column({ type: "timestamp", nullable: true })
    deliveredAt?: Date;

    @Column({ type: "timestamp", nullable: true })
    readAt?: Date;

    @Column({ type: "boolean", default: false })
    isDeleted!: boolean;

    @CreateDateColumn()
    createdAt!: Date;
}
