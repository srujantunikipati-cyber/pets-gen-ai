import { readdirSync } from "fs";
import path from "path";
import { runSeedFileOnce } from "../utils/seedHelper";

const SEEDS_DIR = path.join(__dirname);

export async function runAllSeeds() {
  console.log("🟩 Seed directory:", SEEDS_DIR);

  const seedFiles = readdirSync(SEEDS_DIR).filter(
    (file) =>
      (file.endsWith(".ts") || file.endsWith(".js")) &&
      !file.startsWith("index")
  );

  console.log("🟩 Found seed files:", seedFiles);

  for (const file of seedFiles) {
    try {
      const seedPath = path.join(SEEDS_DIR, file);
      console.log("▶ Running seed:", seedPath);

      const module = await import(seedPath);
      const seedFunction = module.default || Object.values(module)[0];

      if (typeof seedFunction !== "function") {
        console.warn(`⚠️ No valid seed function exported in ${file}`);
        continue;
      }

      await runSeedFileOnce(file.replace(/\.(ts|js)$/, ""), seedFunction);

    } catch (err) {
      console.error(`❌ Error running seed ${file}:`, err);
    }
  }
}
