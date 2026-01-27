// src/config/mongodb.ts
import mongoose from 'mongoose';
import dotenv from "dotenv";

dotenv.config();
export const connectMongoDB = async () => {
  try {
    const mongoUri = process.env.MONGODB_URI;
    console.log('MongoDB URI:', mongoUri);
    if (!mongoUri) {
      throw new Error("MONGODB_URI environment variable is not defined");
    }
    await mongoose.connect(mongoUri);
    console.log('MongoDB connected successfully!');
  } catch (error) {
    console.error('MongoDB connection error:', error);
    process.exit(1);
  }
};

