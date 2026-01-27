import { DataSource } from "typeorm";
import { User } from "../entities/User";
import { logger } from "../utils/logger";
import dotenv from "dotenv";
import { MasterLoginType } from "../entities/MasterLoginType";
import { Conversation } from "../entities/Conversation";
import { MessageMetadata } from "../entities/MessageMetadata";

dotenv.config();

logger.info(`🔄 Initializing PostgreSQL DataSource`);
const dbUrl = process.env.DATABASE_URL || '';
logger.info(`📍 Database Host: ${dbUrl.includes('@') ? dbUrl.split('@')[1].split('/')[0] : 'NOT SET'}`);
logger.info(`📍 Database Name: ${dbUrl.includes('/') ? dbUrl.split('/').pop()?.split('?')[0] : 'NOT SET'}`);

export const AppDataSource = new DataSource({
  type: "postgres",
  url: process.env.DATABASE_URL,
  ssl: false, // <—— important
  entities: [User, MasterLoginType, Conversation, MessageMetadata],
  synchronize: true,
  logging: true,

});


// Initialize database connection with better error handling
(async () => {
  try {
    logger.info(`⏳ Attempting to connect to PostgreSQL...`);
    await AppDataSource.initialize();
    logger.info(`✅ PostgreSQL database connection successful`);
    logger.info(`✅ Database is ready for queries`);
  } catch (error: any) {
    logger.error(`❌ PostgreSQL connection failed:`, error.message);
    logger.error(`Error code: ${error.code}`);

    // Don't crash the app, but log the issue
    // In production, you might want to notify admins or use fallback DB
    process.exit(1);
  }
})();
