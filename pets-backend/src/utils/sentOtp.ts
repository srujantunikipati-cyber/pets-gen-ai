// src/services/otp.service.ts

import { sendEmail } from "../utils/emailService";
import { logger } from "../utils/logger";

// src/utils/otpGenerator.ts
export function generateOTP(): string {
  return Math.floor(100000 + Math.random() * 900000).toString();
}

export async function sendOTPEmail(email: string) {
  const otp = generateOTP();

  // DEVELOPMENT ONLY: Log OTP to console for testing when email fails
  logger.info(`🔢 DEBUG OTP CODE: [ ${otp} ]`);

  const payload = {
    subject: 'Your OTP Code',
    text: `Your OTP code is: ${otp}`,
    html: `<p>Your OTP code is: <strong>${otp}</strong></p>`,
  };

  try {
    logger.info(`💌 Sending OTP email to: ${email}`);
    await sendEmail([email], payload);
    logger.info(`✅ OTP email sent successfully to: ${email}`);
  } catch (err: any) {
    logger.error(`❌ Failed to send OTP email to: ${email} - ${err.message || err}`);
    throw err;
  }

  return otp;
}
