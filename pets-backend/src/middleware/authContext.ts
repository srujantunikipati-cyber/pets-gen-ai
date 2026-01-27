import admin from "../config/firebase";
import { getDBRepository } from "../db/repository";
import { User } from "../entities/User";
import { logger } from "../utils/logger";

type Req = any;
export interface UserContext{
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  username: string;
  firebaseId: string;
  dob?: string;
  phoneNumber?: string;
  isVerified: boolean;
}

/**
 * Build GraphQL context by verifying an incoming Firebase ID token (if present).
 * - Accepts Bearer token in `Authorization` header, `idtoken` header, or `idToken` query param.
 * - Verifies with Firebase Admin SDK and looks up the user in PostgreSQL.
 * - Returns `{ req, res, currentUser }` where `currentUser` is null if verification fails.
 */
export async function authContext({ req, res }: { req: Req; res: any }) {
  let currentUser:UserContext  | null = null;

  try {
    // If this is a GraphQL request for a public operation (login/signup/OTP flows), skip verification
    const publicOperations = new Set([
      "login",
      "createUser",
      "verifyOtpForSignup",
      "SendOtpForSignup",
      "resendEmailVerificationOtp",
      "sendPasswordResetEmail",
      "signupWithGoogle",
      "refreshToken",
    ]);

    const opName = req?.body?.operationName || req?.body?.operation || null;
    if (opName && publicOperations.has(opName)) {
      logger.debug(`Skipping authContext verification for public operation: ${opName}`);
      return { req, res, currentUser: null };
    }

    const headers = req?.headers || {};
    const authHeader = headers.authorization || headers.Authorization;
    let token: string | undefined;

    if (authHeader && typeof authHeader === "string" && authHeader.startsWith("Bearer ")) {
      token = authHeader.split(" ")[1];
    } else if (headers.idtoken) {
      token = headers.idtoken as string;
    } else if (req?.query?.idToken) {
      token = req.query.idToken as string;
    }

    if (!token) {
      logger.debug("No auth token found in request");
      return { req, res, currentUser: null };
    }

    logger.info("🔍 Verifying idToken from request context");
    const decoded = await admin.auth().verifyIdToken(token);
    logger.info(`✅ idToken verified (uid=${decoded.uid})`);

    // Try to find user by firebaseId first, then by email
    const repo = getDBRepository(User);
    const user = await repo.findOne({ where: [{ firebaseId: decoded.uid }, { email: decoded.email }] });
    if (user) {
      currentUser = {
        id: user.id,
        firstName: user.firstName,
        lastName: user.lastName,
        email: user.email,
        username: user.username,
        firebaseId: user.firebaseId,
        dob: user.dob,
        phoneNumber: user.phoneNumber,
        isVerified: user.isVerified,
      };
      logger.info(`✅ Loaded user into context: ${user.email}`);
    } else {
      logger.warn(`⚠️ Token valid but no DB user found for uid=${decoded.uid}`);
    }
  } catch (err: any) {
    logger.warn(`⚠️ authContext token verification failed: ${err?.message}`);
    currentUser = null; // silently ignore token errors for context
  }

  return { req, res, currentUser };
}
