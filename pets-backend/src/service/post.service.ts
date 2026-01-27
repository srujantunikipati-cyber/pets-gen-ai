import { Post } from '../model/postSchema';
import { Like } from '../model/likeSchema';
import { Comment } from '../model/commentSchema';
import { Notification } from '../model/notificationSchema';
import { FollowService } from './follow.service';
import { logger } from '../utils/logger';

export class PostService {
    private followService = new FollowService();
    async createPost(userId: string, contentUrl: string, type: string, caption?: string) {
        try {
            const validTypes = ['video', 'image'];
            if (!validTypes.includes(type)) {
                throw new Error("Invalid post type. Must be 'video' or 'image'");
            }

            const newPost = await Post.create({
                userId,
                contentUrl,
                type,
                caption,
                stats: {
                    likeCount: 0,
                    commentCount: 0,
                    shareCount: 0
                }
            });
            logger.info(`📝 Post created by user ${userId}`);
            return newPost;
        } catch (error: any) {
            logger.error(`❌ Error creating post: ${error.message}`);
            throw error;
        }
    }

    async getFeed(currentUserId: string, limit: number = 20, offset: number = 0) {
        try {
            // Get users the current user follows
            const followingIds = await this.followService.getFollowingIds(currentUserId);
            // Include own posts
            followingIds.push(currentUserId);

            const posts = await Post.find({ userId: { $in: followingIds } })
                .sort({ createdAt: -1 })
                .skip(offset)
                .limit(limit)
                .lean();

            // Enrich with "isLikedByMe"
            const postIds = posts.map(p => p._id);

            // Find which ones the current user liked
            const userLikes = await Like.find({
                userId: currentUserId,
                postId: { $in: postIds }
            }).select('postId');

            const likedPostIds = new Set(userLikes.map(l => l.postId.toString()));

            return posts.map(post => ({
                ...post,
                _id: post._id.toString(),
                isLikedByMe: likedPostIds.has(post._id.toString())
            }));

        } catch (error: any) {
            logger.error(`❌ Error fetching feed: ${error.message}`);
            throw error;
        }
    }

    async toggleLike(userId: string, postId: string) {
        try {
            // Check if post exists
            const post = await Post.findById(postId);
            if (!post) throw new Error("Post not found");

            const existingLike = await Like.findOne({ userId, postId });

            if (existingLike) {
                // Unlike
                await Like.findByIdAndDelete(existingLike._id);
                // Atomic decrement
                const updatedPost = await Post.findByIdAndUpdate(
                    postId,
                    { $inc: { 'stats.likeCount': -1 } },
                    { new: true }
                );
                return { isLiked: false, stats: updatedPost?.stats };
            } else {
                // Like
                await Like.create({ userId, postId });
                // Atomic increment
                const updatedPost = await Post.findByIdAndUpdate(
                    postId,
                    { $inc: { 'stats.likeCount': 1 } },
                    { new: true }
                );

                // Notify author if liker is not author
                if (post.userId !== userId) {
                    await Notification.create({
                        recipientId: post.userId,
                        actorId: userId,
                        type: 'LIKE',
                        entityId: postId
                    });
                }

                return { isLiked: true, stats: updatedPost?.stats };
            }
        } catch (error: any) {
            logger.error(`❌ Error toggling like: ${error.message}`);
            throw error;
        }
    }

    async addComment(userId: string, postId: string, text: string) {
        try {
            // Check if post exists
            const post = await Post.findById(postId);
            if (!post) throw new Error("Post not found");

            const comment = await Comment.create({ userId, postId, text });

            // Increment comment count
            await Post.findByIdAndUpdate(postId, { $inc: { 'stats.commentCount': 1 } });

            // Notify author
            if (post.userId !== userId) {
                await Notification.create({
                    recipientId: post.userId,
                    actorId: userId,
                    type: 'COMMENT',
                    entityId: postId
                });
            }

            return comment;
        } catch (error: any) {
            logger.error(`❌ Error adding comment: ${error.message}`);
            throw error;
        }
    }

    async getComments(postId: string, limit: number = 50, offset: number = 0) {
        try {
            return await Comment.find({ postId })
                .sort({ createdAt: 1 })
                .skip(offset)
                .limit(limit);
        } catch (error: any) {
            logger.error(`❌ Error fetching comments: ${error.message}`);
            throw error;
        }
    }

    async trackShare(postId: string) {
        try {
            const updatedPost = await Post.findByIdAndUpdate(
                postId,
                { $inc: { 'stats.shareCount': 1 } },
                { new: true }
            );
            return updatedPost?.stats;
        } catch (error: any) {
            logger.error(`❌ Error tracking share: ${error.message}`);
            throw error;
        }
    }

    async getNotifications(userId: string, limit: number = 20, offset: number = 0) {
        try {
            return await Notification.find({ recipientId: userId })
                .sort({ createdAt: -1 })
                .skip(offset)
                .limit(limit);
        } catch (error: any) {
            logger.error(`❌ Error fetching notifications: ${error.message}`);
            throw error;
        }
    }
}
