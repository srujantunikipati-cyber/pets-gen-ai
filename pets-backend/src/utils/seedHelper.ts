import { SeedRun } from "../model/seedFileSchema";
import { logger } from "./logger"; // adjust path if needed

export async function runSeedFileOnce(seedFileName: string, seedFunction: () => Promise<void>) {
  const alreadyRun = await SeedRun.findOne({ seedName: seedFileName });

  if (alreadyRun) {
    logger.info(`ℹ️ Seed "${seedFileName}" already executed at ${alreadyRun.runAt}`);
    return;
  }

  logger.info(`🔄 Running seed "${seedFileName}"...`);
  await seedFunction();

  await SeedRun.create({ seedName: seedFileName, runAt: new Date() });
  logger.info(`✅ Seed "${seedFileName}" executed successfully`);
}
