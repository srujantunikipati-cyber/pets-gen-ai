import { Resolver, Mutation, Query, Arg, Int } from "type-graphql";
import { PostService } from "../service/post.service";
import {
    PostResponse,
    CreatePostInput,
    FeedPayload,
    SinglePostPayload,
    LikePayload,
    CommentPayload,
    CommentsListPayload,
    NotificationListPayload,
    SharePayload
} from "./dto/postResolverDto";
import ApiResponse from "../utils/response";
import { logger } from "../utils/logger";

@Resolver()
export class PostResolver {
    private postService = new PostService();

    @Mutation(() => SinglePostPayload)
    async createPost(
        @Arg("input") input: CreatePostInput
    ): Promise<SinglePostPayload> {
        try {
            const post = await this.postService.createPost(
                input.userId,
                input.contentUrl,
                input.type,
                input.caption
            );
            return ApiResponse.success(post, "Post created successfully");
        } catch (error: any) {
            logger.error(`❌ createPost error: ${error.message}`);
            return ApiResponse.error(error.message || "Internal Server Error", 500);
        }
    }

    @Query(() => FeedPayload)
    async getFeed(
        @Arg("userId") userId: string,
        @Arg("limit", () => Int, { nullable: true }) limit?: number,
        @Arg("offset", () => Int, { nullable: true }) offset?: number
    ): Promise<FeedPayload> {
        try {
            const posts = await this.postService.getFeed(userId, limit, offset);
            return ApiResponse.success(posts, "Feed fetched successfully");
        } catch (error: any) {
            logger.error(`❌ getFeed error: ${error.message}`);
            return ApiResponse.error(error.message || "Internal Server Error", 500);
        }
    }

    @Mutation(() => LikePayload)
    async toggleLike(
        @Arg("userId") userId: string,
        @Arg("postId") postId: string
    ): Promise<LikePayload> {
        try {
            const result = await this.postService.toggleLike(userId, postId);
            return ApiResponse.success(result, result.isLiked ? "Post liked" : "Post unliked");
        } catch (error: any) {
            logger.error(`❌ toggleLike error: ${error.message}`);
            return ApiResponse.error(error.message || "Internal Server Error", 500);
        }
    }

    @Mutation(() => CommentPayload)
    async addComment(
        @Arg("userId") userId: string,
        @Arg("postId") postId: string,
        @Arg("text") text: string
    ): Promise<CommentPayload> {
        try {
            const comment = await this.postService.addComment(userId, postId, text);
            return ApiResponse.success(comment, "Comment added successfully");
        } catch (error: any) {
            logger.error(`❌ addComment error: ${error.message}`);
            return ApiResponse.error(error.message || "Internal Server Error", 500);
        }
    }

    @Query(() => CommentsListPayload)
    async getComments(
        @Arg("postId") postId: string,
        @Arg("limit", () => Int, { nullable: true }) limit?: number,
        @Arg("offset", () => Int, { nullable: true }) offset?: number
    ): Promise<CommentsListPayload> {
        try {
            const comments = await this.postService.getComments(postId, limit, offset);
            return ApiResponse.success(comments, "Comments fetched successfully");
        } catch (error: any) {
            logger.error(`❌ getComments error: ${error.message}`);
            return ApiResponse.error(error.message || "Internal Server Error", 500);
        }
    }

    @Mutation(() => SharePayload)
    async trackShare(
        @Arg("postId") postId: string
    ): Promise<SharePayload> {
        try {
            const stats = await this.postService.trackShare(postId);
            return ApiResponse.success(stats, "Share tracked successfully");
        } catch (error: any) {
            logger.error(`❌ trackShare error: ${error.message}`);
            return ApiResponse.error(error.message || "Internal Server Error", 500);
        }
    }

    @Query(() => NotificationListPayload)
    async getNotifications(
        @Arg("userId") userId: string,
        @Arg("limit", () => Int, { nullable: true }) limit?: number,
        @Arg("offset", () => Int, { nullable: true }) offset?: number
    ): Promise<NotificationListPayload> {
        try {
            const notifications = await this.postService.getNotifications(userId, limit, offset);
            return ApiResponse.success(notifications, "Notifications fetched successfully");
        } catch (error: any) {
            logger.error(`❌ getNotifications error: ${error.message}`);
            return ApiResponse.error(error.message || "Internal Server Error", 500);
        }
    }
}
