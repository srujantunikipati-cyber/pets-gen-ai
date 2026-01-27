import { Schema, model, Document } from "mongoose";

export interface ISeedRun extends Document {
  seedName: string; // the file name of the seed, e.g., "123_emailtemplateInsert"
  runAt: Date;
}

const SeedRunSchema = new Schema<ISeedRun>({
  seedName: { type: String, required: true, unique: true },
  runAt: { type: Date, required: true, default: () => new Date() }
});

export const SeedRun = model<ISeedRun>("SeedRun", SeedRunSchema);
