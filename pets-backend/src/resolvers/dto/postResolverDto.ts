import { ObjectType, Field, ID, InputType, Int } from "type-graphql";

// --- Types ---
@ObjectType()
export class PostStats {
    @Field(() => Int)
    likeCount!: number;

    @Field(() => Int)
    commentCount!: number;

    @Field(() => Int)
    shareCount!: number;
}

@ObjectType()
export class PostResponse {
    @Field(() => ID)
    _id!: string;

    @Field()
    userId!: string;

    @Field()
    contentUrl!: string;

    @Field({ nullable: true })
    caption?: string;

    @Field()
    type!: string;

    @Field(() => PostStats)
    stats!: PostStats;

    @Field()
    createdAt!: Date;

    @Field({ nullable: true })
    isLikedByMe?: boolean;
}

// --- Inputs ---

@InputType()
export class CreatePostInput {
    @Field()
    userId!: string;

    @Field()
    contentUrl!: string;

    @Field()
    type!: string; // 'video' or 'image'

    @Field({ nullable: true })
    caption?: string;
}

// --- Payload Wrappers (for standardized responses) ---

@ObjectType()
export class SinglePostPayload {
    @Field()
    status!: boolean;

    @Field()
    code!: number;

    @Field()
    message!: string;

    @Field(() => PostResponse, { nullable: true })
    data?: PostResponse;
}

@ObjectType()
export class FeedPayload {
    @Field()
    status!: boolean;

    @Field()
    code!: number;

    @Field()
    message!: string;

    @Field(() => [PostResponse], { nullable: true })
    data?: PostResponse[];
}

@ObjectType()
export class LikeData { // Payload data for like toggle
    @Field()
    isLiked!: boolean;

    @Field(() => PostStats)
    stats!: PostStats;
}

@ObjectType()
export class LikePayload {
    @Field()
    status!: boolean;

    @Field()
    code!: number;

    @Field()
    message!: string;

    @Field(() => LikeData, { nullable: true })
    data?: LikeData;
}

@ObjectType()
export class CommentObject {
    @Field(() => ID)
    _id!: string;

    @Field()
    userId!: string;

    @Field()
    postId!: string;

    @Field()
    text!: string;

    @Field()
    createdAt!: Date;
}

@ObjectType()
export class CommentPayload {
    @Field()
    status!: boolean;

    @Field()
    code!: number;

    @Field()
    message!: string;

    @Field(() => CommentObject, { nullable: true })
    data?: CommentObject;
}

@ObjectType()
export class CommentsListPayload {
    @Field()
    status!: boolean;

    @Field()
    code!: number;

    @Field()
    message!: string;

    @Field(() => [CommentObject], { nullable: true })
    data?: CommentObject[];
}

@ObjectType()
export class NotificationObject {
    @Field(() => ID)
    _id!: string;

    @Field()
    recipientId!: string;

    @Field()
    actorId!: string;

    @Field()
    type!: string;

    @Field()
    entityId!: string;

    @Field()
    isRead!: boolean;

    @Field()
    createdAt!: Date;
}

@ObjectType()
export class NotificationListPayload {
    @Field()
    status!: boolean;

    @Field()
    code!: number;

    @Field()
    message!: string;

    @Field(() => [NotificationObject], { nullable: true })
    data?: NotificationObject[];
}

@ObjectType()
export class SharePayload {
    @Field()
    status!: boolean;

    @Field()
    code!: number;

    @Field()
    message!: string;

    @Field(() => PostStats, { nullable: true })
    data?: PostStats;
}
