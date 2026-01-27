import { UserOTP } from "../model/userOtpSchema";

export class UserOTPRepository {
  create(arg0: { userId: string; type: string; otp: string; expireAt: number; createdAt: number; }) {
    throw new Error("Method not implemented.");
  }
  /**
   * Delete all OTPs for a user & type
   */
  async deleteByUserAndType(userId: string, type: string) {
    return await UserOTP.deleteMany({ userId, type });
  }

  /**
   * Create a new OTP record
   */
  async createOtp(userId: string, type: string, otp: string, expireAt: number) {
    return await  UserOTP.create({ userId, type, otp, expireAt });
   
  }



  /**
   * Find OTP by userId, otp value, and type
   */
  async findOtp(userId: string, otp: string, type: string) {
    return await UserOTP.findOne({ userId, otp, type });
  }

  /**
   * Delete OTP by ID
   */
  async deleteById(id: string) {
    return await UserOTP.deleteOne({ _id: id });
  }
}
