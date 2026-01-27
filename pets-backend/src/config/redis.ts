import Redis from "ioredis";
import { logger } from "../utils/logger";

class RedisClient {
    private static instance: Redis | null = null;

    static getInstance(): Redis {
        if (!RedisClient.instance) {
            const redisHost = process.env.REDIS_HOST || "localhost";
            const redisPort = parseInt(process.env.REDIS_PORT || "6379", 10);
            const redisPassword = process.env.REDIS_PASSWORD || undefined;
            const redisDb = parseInt(process.env.REDIS_DB || "0", 10);

            RedisClient.instance = new Redis({
                host: redisHost,
                port: redisPort,
                password: redisPassword,
                db: redisDb,
                retryStrategy: (times) => {
                    const delay = Math.min(times * 50, 2000);
                    return delay;
                },
                maxRetriesPerRequest: 3,
            });

            RedisClient.instance.on("connect", () => {
                logger.info("✅ Redis connected successfully");
            });

            RedisClient.instance.on("error", (err) => {
                logger.error(`❌ Redis error: ${err.message}`);
            });

            RedisClient.instance.on("reconnecting", () => {
                logger.warn("⚠️ Redis reconnecting...");
            });
        }

        return RedisClient.instance;
    }

    static async disconnect(): Promise<void> {
        if (RedisClient.instance) {
            await RedisClient.instance.quit();
            RedisClient.instance = null;
            logger.info("Redis disconnected");
        }
    }
}

export const redisClient = RedisClient.getInstance();
export default RedisClient;
