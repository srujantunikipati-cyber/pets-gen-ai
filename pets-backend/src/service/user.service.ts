import { getDBRepository } from "../db/repository";
import { User } from "../entities/User";
import { GoogleSignupArgs, SignupArgs, UpdateProfileInput, UserResponseDto } from "../resolvers/dto/userResolverDto";
import { sendOTPEmail } from "../utils/sentOtp";
import { UserOTP } from "../model/userOtpSchema";
import admin from "../config/firebase";
import axios from "axios";
import dotenv from "dotenv";
import { sendEmail } from "../utils/emailService";
import { OAuth2Client } from "google-auth-library";
import { UserOTPRepository } from "../repository/UserOTPRepository";
import { logger } from "../utils/logger";
import { HttpStatusCodes, LoginType } from "../utils/constant";
import { TemplateService } from "../utils/templateService";
import { UserContext } from "../middleware/authContext";

dotenv.config();

const FIREBASE_API_KEY = process.env.FIREBASE_API_KEY!;
const client = new OAuth2Client(process.env.GOOGLE_CLIENT_ID);

interface ServiceError extends Error {
  status?: number;
}

export class UserService {
  private userRepo = getDBRepository(User);
  private userOTPRepo = new UserOTPRepository();

  private createError(message: string, status = HttpStatusCodes.INTERNAL_SERVER_ERROR): ServiceError {
    const error = new Error(message) as ServiceError;
    error.status = status;
    return error;
  }

  async createUser(args: SignupArgs) {
    const { firstName, lastName, email, password, dob, phoneNumber } = args;
    let username = args.username;
    logger.info(`🔄 Starting user signup for email: ${email}`);

    try {
      const existing = await this.userRepo.findOne({ where: { email } });
      console.log("existing", existing);
      if (existing) {
        logger.warn(`⚠️ User already exists: ${email} existing.isVerified ${existing}`, existing.isVerified);
        if (existing.isVerified) {
          throw this.createError("User already exists", HttpStatusCodes.CONFLICT); // 409
        }
        logger.info(`ℹ️ Existing unverified user. Resending verification OTP to ${email}`);
        // await this.updatePassword(existing.firebaseId!, password);
        return await this.resendEmailVerificationOtp(email);
        // throw this.createError("User already exists", HttpStatusCodes.CONFLICT); // 409
      }


      // ------- UNIQUE USERNAME GENERATION -------
      let uniqueUsername = username;


      username = await this.generateUniqueUsername(this.userRepo, uniqueUsername)

      logger.info(`✅ Unique username generated: ${username}`);
     logger.info(`✅ password username : ${password}`);
      const userRecord = await admin.auth().createUser({ email, password, displayName: `${firstName} ${lastName}` });
      logger.info(`✅ Firebase user created with UID: ${userRecord.uid}`);

      const verificationLink = await admin.auth().generateEmailVerificationLink(email);
      logger.info(`✅ Verification link generated`);

      const otp = await sendOTPEmail(email);
      logger.info(`✅ OTP sent successfully`);

      const ttlMinutes = 10;
      const expireAt = Date.now() + ttlMinutes * 60 * 1000;

      await UserOTP.create({ userId: email, type: "signup_email_verification", otp, expireAt, createdAt: Date.now() });
      logger.info(`✅ OTP record saved successfully`);

      const user = this.userRepo.create({
        firebaseId: userRecord.uid,
        firstName,
        lastName,
        username,
        email,
        dob,
        phoneNumber,
        isVerified: false,
        loginTypeId: LoginType.manualy
      });
      await this.userRepo.save(user);
      logger.info(`✅ User saved to PostgreSQL successfully`);

      return { user, verificationLink };
    } catch (error: any) {
      logger.error(`❌ Signup error for ${email}: ${error.message}`, error);
      throw this.createError(error.message, error.status || HttpStatusCodes.INTERNAL_SERVER_ERROR);
    }
  }

  async login(email: string, password: string) {
    logger.info(`🔄 Login attempt for email: ${email} ${password}`);

    try {
      const user = await this.userRepo.findOne({ where: { email } });
      if (!user) throw this.createError("User not found. Please sign up first.", HttpStatusCodes.NOT_FOUND); // 404
       logger.info(`🔄 user Found}`);

      if (user.loginTypeId===LoginType.google) throw this.createError("Force To Change the Password.", HttpStatusCodes.FORCECHANGE_PASSWORD); // 404
       logger.info(`🔄 user Found Force To Change the Password}`);

      if (!user.isVerified) throw this.createError("Email is not verified. Please verify your email first.", HttpStatusCodes.FORBIDDEN); // 403
    logger.info(`🔄 user isVerified ${  password} ${email}`);
      const response = await axios.post(
        `https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=${FIREBASE_API_KEY}`,
        { email, password, returnSecureToken: true }
      );

      return {
        idToken: response.data.idToken,
        refreshToken: response.data.refreshToken,
        uid: response.data.localId,
        email: response.data.email,
      };
    } catch (error: any) {
      logger.error(`❌ Login error for ${email}: ${error.message}`, error);

      const firebaseMsg = error.response?.data?.error?.message;
      if (firebaseMsg) throw this.createError(firebaseMsg, HttpStatusCodes.BAD_REQUEST);

      throw this.createError(error.message, error.status || HttpStatusCodes.INTERNAL_SERVER_ERROR);
    }
  }

async deleteUserProfile(user: UserContext) {
  logger.info(`🔄 Attempting to delete profile for email: ${user}`);

  try {
    // 1️⃣ Fetch user from PostgreSQL
   

    const firebaseUid = user.firebaseId;
    logger.info(`✅ Firebase login successful for UID: ${firebaseUid}`);

    // 3️⃣ Delete user from Firebase Auth
    await admin.auth().deleteUser(firebaseUid);
    logger.info(`✅ Firebase user deleted: ${firebaseUid}`);

    // 4️⃣ Delete user from PostgreSQL
    await this.userRepo.delete({ firebaseId: firebaseUid });
    logger.info(`✅ User deleted from PostgreSQL: ${firebaseUid}`);

  await this.deleteAllUsers()
    return {
      status: true,
      code: 200,
      message: "User profile deleted successfully",
    };
  } catch (error: any) {
    logger.error(`❌ Delete profile error for : ${error.message}`, error);

    const firebaseMsg = error.response?.data?.error?.message;
    if (firebaseMsg)
      throw this.createError(firebaseMsg, 400);

    throw this.createError(
      error.message || "Failed to delete profile",
      error.status || 500
    );
  }
}
async deleteAllUsers() {
  logger.info("🗑️ Starting full user deletion process...");

  try {
    // -----------------------------------------
    // 1️⃣ FETCH ALL FIREBASE USERS
    // -----------------------------------------
    let nextPageToken: string | undefined = undefined;
    const firebaseUIDs: string[] = [];

    do {
      const listUsersResult = await admin.auth().listUsers(1000, nextPageToken);

      listUsersResult.users.forEach(user => {
        firebaseUIDs.push(user.uid);
      });

      nextPageToken = listUsersResult.pageToken;
    } while (nextPageToken);

    logger.info(`🔍 Total Firebase users found: ${firebaseUIDs.length}`);


    // -----------------------------------------
    // 2️⃣ DELETE USERS FROM FIREBASE IN BATCHES
    // -----------------------------------------
    const batchSize = 100;
    for (let i = 0; i < firebaseUIDs.length; i += batchSize) {
      const batch = firebaseUIDs.slice(i, i + batchSize);
      const result = await admin.auth().deleteUsers(batch);

      logger.info(
        `🔥 Firebase batch deleted: ${batch.length}, success: ${result.successCount}, failed: ${result.failureCount}`
      );
    }

    logger.info("✅ All Firebase users deleted successfully");


    // -----------------------------------------
    // 3️⃣ DELETE FROM POSTGRESQL users TABLE
    // -----------------------------------------
    await this.userRepo.createQueryBuilder().delete().from(User).execute();
    logger.info("🗑️ All users deleted from PostgreSQL table successfully");


    // -----------------------------------------
    // 4️⃣ DELETE OTP TABLE (optional)
    // -----------------------------------------
     await UserOTP.deleteMany({});

    logger.info("🗑️ All OTP records deleted successfully");


    return { success: true, message: "All users deleted from Firebase + PostgreSQL" };

  } catch (error: any) {
    logger.error(`❌ Error deleting all users: ${error.message}`, error);
    throw this.createError(error.message, error.status || HttpStatusCodes.INTERNAL_SERVER_ERROR);
  }
}


  async verifyToken(idToken: string) {
    logger.info(`🔍 Verifying ID token`);
    try {
      const decodedToken = await admin.auth().verifyIdToken(idToken);
      return { uid: decodedToken.uid, email: decodedToken.email! };
    } catch (error: any) {
      logger.error(`❌ Token verification failed: ${error.message}`, error);
      throw this.createError(error.message, HttpStatusCodes.UNAUTHORIZED); // 401
    }
  }

  async refreshToken(refreshToken: string) {
    logger.info(`🔄 Refreshing Firebase token`);
    try {
      const url = `https://securetoken.googleapis.com/v1/token?key=${FIREBASE_API_KEY}`;
      const response = await axios.post(url, { grant_type: "refresh_token", refresh_token: refreshToken });
      return { idToken: response.data.id_token, refreshToken: response.data.refresh_token, uid: response.data.user_id, email: "" };
    } catch (err: any) {
      logger.error(`❌ Token refresh failed: ${err.message}`, err);
      throw this.createError(err.response?.data?.error?.message || "Failed to refresh token", HttpStatusCodes.BAD_REQUEST);
    }
  }

  async generatePasswordResetLink(email: string): Promise<string> {
    logger.info(`🔐 Generating password reset link for: ${email}`);
    try {
      const resetLink = await admin.auth().generatePasswordResetLink(email);
      const restLinkTemplate = await TemplateService.renderTemplate("petsnapchat_password_reset", {
        USERNAME: "John Doe",
        RESET_LINK: resetLink
      });
      await sendEmail([email], { subject: restLinkTemplate.subject, text: restLinkTemplate.text, html: restLinkTemplate.html });
      return "Password reset link sent to email";
    } catch (err: any) {
      logger.error(`❌ Password reset failed for ${email}: ${err.message}`, err);
      throw this.createError(err.message || "Failed to generate password reset link", HttpStatusCodes.INTERNAL_SERVER_ERROR);
    }
  }

  async loginOrSignupWithGoogle(args: GoogleSignupArgs): Promise<{ firebaseToken: string }> {
    const { idToken, dob, phoneNumber } = args;

    try {
      // 1️⃣ Verify Google ID token
      const ticket = await client.verifyIdToken({
        idToken,
        audience: process.env.GOOGLE_CLIENT_ID,
      });
      const payload = ticket.getPayload();
      if (!payload || !payload.email) {
        throw this.createError("Google account has no email", 400);
      }

      const { sub: googleUid, email, name, picture } = payload;

      // 2️⃣ Check PostgreSQL for existing verified user
      let user = await this.userRepo.findOne({ where: { email, isVerified: true } });
      if (user) {
        // Update the loginTypeId
        user.loginTypeId = LoginType.manualy_google; // set to your desired FK

        // Save the changes
        await this.userRepo.save(user);

        logger.info(`✅ Updated loginTypeId for user ${email} to ${LoginType.manualy_google}`);
      }
      let firebaseUser;
      try {
        // Try to get Firebase user by email
        firebaseUser = await admin.auth().getUserByEmail(email);
      } catch (err: any) {
        if (err.code === "auth/user-not-found") {
          // Create Firebase user if not exists
          firebaseUser = await admin.auth().createUser({
            uid: googleUid,
            email,
            displayName: name,
            photoURL: picture,
          });
          logger.info(`✅ Firebase user created: ${email}`);
        } else throw err;
      }

      // 3️⃣ Create PostgreSQL user if not exists
      if (!user) {
        user = this.userRepo.create({
          firebaseId: firebaseUser.uid,
          firstName: name || "",
          lastName: "",
          username: email.split("@")[0],
          email,
          dob,
          phoneNumber,
          isVerified: true,
          loginTypeId: LoginType.google
        });
        await this.userRepo.save(user);
        logger.info(`✅ User saved in PostgreSQL: ${email}`);
      }


      // 4️⃣ Generate custom Firebase token
      const customToken = await admin.auth().createCustomToken(firebaseUser.uid);

      return { firebaseToken: customToken };
    } catch (error: any) {
      logger.error(`❌ Google login/signup failed: ${error.message}`, error);
      throw this.createError(error.message, error.status || 500);
    }
  }


  async resendEmailVerificationOtp(email: string): Promise<{ otp: string }> {
    logger.info(`🔄 Resending email verification OTP for: ${email}`);
    try {
      const type = "signup_email_verification";
      await this.userOTPRepo.deleteByUserAndType(email, type);

      const otp = await sendOTPEmail(email);

      const ttlMinutes = 10;
      const expireAt = Date.now() + ttlMinutes * 60 * 1000;

      await UserOTP.create({ userId: email, type: "signup_email_verification", otp, expireAt, createdAt: Date.now() });

      return { otp };
    } catch (error: any) {
      logger.error(`❌ Resend OTP failed for ${email}: ${error.message}`, error);
      throw this.createError(error.message, error.status || HttpStatusCodes.INTERNAL_SERVER_ERROR);
    }
  }

  async getUsers(): Promise<UserResponseDto[]> {
    logger.info(`📊 Fetching all users from database`);
    try {
      const users = await this.userRepo.find();
      return users.map(user => ({
        id: user.id,
        firstName: user.firstName,
        lastName: user.lastName,
        email: user.email,
        username: user.username,
        phoneNumber: user.phoneNumber,
        dob: user.dob,
        isVerified: user.isVerified,
      }));
    } catch (error: any) {
      logger.error(`❌ Failed to fetch users: ${error.message}`, error);
      throw this.createError(error.message, error.status || HttpStatusCodes.INTERNAL_SERVER_ERROR);
    }
  }

  async updateProfile(userId: string, input: UpdateProfileInput): Promise<UserResponseDto> {
    logger.info(`🔄 Updating profile for userId: ${userId}`);
    try {
      // 1️⃣ Find user by ID
      const user = await this.userRepo.findOne({ where: { id: userId } });
      if (!user) {
        logger.warn(`⚠️ User not found: ${userId}`);
        throw this.createError("User not found", HttpStatusCodes.NOT_FOUND);
      }

      // 2️⃣ Update only the provided fields
      if (input.firstName !== undefined) user.firstName = input.firstName;
      if (input.lastName !== undefined) user.lastName = input.lastName;
      if (input.dob !== undefined) user.dob = input.dob;
      if (input.phoneNumber !== undefined) user.phoneNumber = input.phoneNumber;

      // 3️⃣ Save updated user
      await this.userRepo.save(user);
      logger.info(`✅ User profile updated successfully: ${userId}`);

      // 4️⃣ Return updated user info
      return {
        id: user.id,
        firstName: user.firstName,
        lastName: user.lastName,
        email: user.email,
        username: user.username,
        phoneNumber: user.phoneNumber,
        dob: user.dob,
        isVerified: user.isVerified,
      };
    } catch (error: any) {
      logger.error(`❌ Failed to update profile for ${userId}: ${error.message}`, error);
      throw this.createError(
        error.message || "Failed to update profile",
        error.status || HttpStatusCodes.INTERNAL_SERVER_ERROR
      );
    }
  }


  //comman function to generate unique username

  async generateUniqueUsername(
    userRepo: any,
    baseUsername: string,
    maxAttempts = 20
  ): Promise<string> {
    let uniqueUsername = baseUsername;
    let attempts = 0;

    while (true) {
      const existingUser = await userRepo.findOne({ where: { username: uniqueUsername } });
      if (!existingUser) break; // Unique → exit loop

      // Generate random 4-digit number
      const randomNum = Math.floor(1000 + Math.random() * 9000);
      uniqueUsername = `${baseUsername}${randomNum}`;
      attempts++;

      logger.warn(`⚠️ Username exists. Trying: ${uniqueUsername}`);

      if (attempts >= maxAttempts) {
        throw new Error("Failed to generate unique username after multiple attempts");
      }
    }

    return uniqueUsername;
  }


async updatePassword(uid: string, newPassword: string): Promise<admin.auth.UserRecord> {
  try {
    const userRecord = await admin.auth().updateUser(uid, {
      password: newPassword
    });

    console.log("✅ Password updated for user:", userRecord.uid);
    return userRecord;

  } catch (error) {
    console.error("❌ Error updating password:", error);
    throw error;
  }
}



}

