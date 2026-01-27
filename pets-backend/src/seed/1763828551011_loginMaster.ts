import { AppDataSource } from "../config/postgres"; // your TypeORM DS
import { MasterLoginType } from "../entities/MasterLoginType";
import { logger } from "../utils/logger";
import { seedData } from "../data/masterLoginData"; // adjust path

export async function seedMasterLoginTypes() {
  try {
    const repo = AppDataSource.getRepository(MasterLoginType);

    logger.info("🗑  Deleting all records from master_login_type...");
    await repo.clear(); // deletes all rows fast

    logger.info("📥 Inserting master login types...");

    for (const item of seedData) {
      const newEntry = repo.create({
        ...item,
        createdAt: new Date(),
      });
      await repo.save(newEntry);
      logger.info(`✅ Inserted: ${item.type}`);
    }

    logger.info("🎉 master_login_type seeding complete!");
  } catch (error) {
    logger.error("❌ Error seeding master_login_type:", error);
  }
}
