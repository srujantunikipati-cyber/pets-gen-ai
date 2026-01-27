// src/models/UserOTP.ts
import  { Schema, Document, model } from 'mongoose';
import { v4 as uuidv4 } from 'uuid'; // works with CommonJS



export interface IUserOTP extends Document {
  cid: string;
  userId: string;
  type: string;
  otp: string;
  expireAt: number;
  createdAt: Date;
}

const userOTPSchema: Schema = new Schema<IUserOTP>(
  {
    cid: { type: String, default: uuidv4 },
    userId: { type: String, required: true },
    type: { type: String, required: true },
    otp: { type: String, required: true },
    expireAt: { type: Number, required: true },
  },
  { timestamps: true }
);

export const UserOTP = model<IUserOTP>('UserOTP', userOTPSchema);
