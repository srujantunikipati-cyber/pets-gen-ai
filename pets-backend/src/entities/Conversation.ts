import {
    Entity,
    PrimaryGeneratedColumn,
    Column,
    CreateDateColumn,
    UpdateDateColumn,
    Index,
} from "typeorm";

@Entity("conversations")
@Index(["participant1Id", "participant2Id"], { unique: true })
export class Conversation {
    @PrimaryGeneratedColumn("uuid")
    id!: string;

    @Column({ type: "varchar" })
    @Index()
    participant1Id!: string;

    @Column({ type: "varchar" })
    @Index()
    participant2Id!: string;

    @Column({ type: "timestamp", nullable: true })
    lastMessageAt?: Date;

    @Column({ type: "varchar", length: 500, nullable: true })
    lastMessagePreview?: string;

    @Column({ type: "boolean", default: false })
    isBlocked!: boolean;

    @Column({ type: "varchar", nullable: true })
    blockedBy?: string;

    @CreateDateColumn()
    createdAt!: Date;

    @UpdateDateColumn()
    updatedAt!: Date;
}
