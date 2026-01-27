import { Follow } from '../model/followSchema';
import { logger } from '../utils/logger';

export class FollowService {
    async followUser(currentUserId: string, targetUserId: string) {
        try {
            if (currentUserId === targetUserId) {
                throw new Error("You cannot follow yourself");
            }

            // Check if already following
            const existingFollow = await Follow.findOne({ followerId: currentUserId, followingId: targetUserId });
            if (existingFollow) {
                return { isFollowing: true, message: "Already following" };
            }

            await Follow.create({
                followerId: currentUserId,
                followingId: targetUserId
            });

            logger.info(`User ${currentUserId} followed ${targetUserId}`);
            return { isFollowing: true, message: "Followed successfully" };
        } catch (error: any) {
            logger.error(`Error in followUser: ${error.message}`);
            throw error;
        }
    }

    async unfollowUser(currentUserId: string, targetUserId: string) {
        try {
            const result = await Follow.findOneAndDelete({
                followerId: currentUserId,
                followingId: targetUserId
            });

            if (!result) {
                return { isFollowing: false, message: "Not following" };
            }

            logger.info(`User ${currentUserId} unfollowed ${targetUserId}`);
            return { isFollowing: false, message: "Unfollowed successfully" };
        } catch (error: any) {
            logger.error(`Error in unfollowUser: ${error.message}`);
            throw error;
        }
    }

    async getFollowingIds(userId: string): Promise<string[]> {
        const follows = await Follow.find({ followerId: userId }).select('followingId');
        return follows.map(f => f.followingId);
    }

    async getFollowerIds(userId: string): Promise<string[]> {
        const follows = await Follow.find({ followingId: userId }).select('followerId');
        return follows.map(f => f.followerId);
    }
}
