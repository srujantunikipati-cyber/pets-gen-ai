// src/resolvers/UserResolver.ts
import { Resolver, Query, Mutation, Args, Ctx } from "type-graphql";
import { UserService } from "../service/user.service";
import {
  SignupArgs,
  UserResponseDto,
  LoginArgs,
  LoginResponseDto,
  RefreshTokenResponse,
  RefreshTokenArgs,
  GoogleSignupArgs,
  CreateUserResponseDto,
  VerifyTokenArgs,
  VerifyTokenResponse,
  BaseResponse,
  SendPasswordResetEmailArgs,
  UserDetailsResponse,
  LoginResponse,
  VerifyTokenFullResponse,
  sendPasswordResetEmailResponse,
  UpdateProfileInput,
  loginOrSignupWithGoogleResponse,
  FollowUserArgs,
} from "./dto/userResolverDto";
import { FollowService } from "../service/follow.service";
import { UserOTP } from "../model/userOtpSchema";
import { VerifyOtpArgs, VerifyOtpResponse } from "./dto/otpResolverDto";
import { getDBRepository } from "../db/repository";
import { User } from "../entities/User";
import { logger } from "../utils/logger";
import ApiResponse from "../utils/response";
import { ErrorResponse, HttpStatusCodes, responseMessage } from "../utils/constant";
import { STATUS_CODES } from "http";
import { CustomGraphQLError } from "../utils/utils";
import { UserContext } from "../middleware/authContext";

@Resolver()
export class UserResolver {
  private userService = new UserService();
  private followService = new FollowService();
  private userRepo = getDBRepository(User);

  @Query(() => [UserResponseDto])
  async getUsers(): Promise<UserResponseDto[]> {
    logger.info(`📊 Query: getUsers`);
    try {
      return await this.userService.getUsers();
    } catch (error: any) {
      logger.error(`❌ getUsers error: ${error.message}`, error);
      throw error;
    }
  }

  @Query(() => UserDetailsResponse) // single object
  async getUsersDetails(@Ctx() ctx: any): Promise<UserDetailsResponse> {
    logger.info(`📊 Query: getUsersDetails`);
    try {
      const currentUser = ctx?.currentUser;
      if (!currentUser) throw new Error("Unauthorized");

      const userDto: UserResponseDto = {
        id: currentUser.id!,
        firstName: currentUser.firstName || "",
        lastName: currentUser.lastName || "",
        name: `${currentUser.firstName || ""} ${currentUser.lastName || ""}`.trim(),
        email: currentUser.email || "",
        username: currentUser.username || "",
        firebaseId: currentUser.firebaseId || "",
        dob: currentUser.dob || "",
        phoneNumber: currentUser.phoneNumber || "",
        isVerified: currentUser.isVerified || false,
      };

      return ApiResponse.success([userDto], "User details fetched successfully");
    } catch (error: any) {
      logger.error(`❌ getUsersDetails error: ${error.message}`, error);
      return ApiResponse.error("Internal Server Error", 500);
    }
  }


  @Mutation(() => LoginResponse)
  async login(@Args() { email, password }: LoginArgs): Promise<LoginResponse> {
    logger.info(`🔐 Mutation: login for email: ${email}`);
    try {
      const result = await this.userService.login(email, password);

      const data = {
        idToken: result.idToken,
        refreshToken: result.refreshToken,
        userId: result.uid,
        email: result.email,
      };
      return ApiResponse.success(data, responseMessage.UserLoginSuccess);
    } catch (error: any) {
      logger.error(
        `❌ Login mutation error for ${email}: ${error.message}`,
        error
      );
      return ApiResponse.error(error.message || ErrorResponse.INTERNAL_SERVER_ERROR, 500);
    }
  }

  @Mutation(() => CreateUserResponseDto)
  async createUser(@Args() User: SignupArgs): Promise<CreateUserResponseDto> {
    logger.info(`📝 Mutation: createUser for email: ${User.email}`);
    try {
      await this.userService.createUser(User);
      return ApiResponse.success(undefined, responseMessage.OtpSendSuccess);
    } catch (error: any) {
      logger.info("Error creating user:", error);
      return ApiResponse.error(error?.message || "Internal Server Error", 500);
    }
  }

  @Mutation(() => VerifyOtpResponse)
  async verifyOtpForSignup(
    @Args() { email, otp }: VerifyOtpArgs
  ): Promise<VerifyOtpResponse> {
    logger.info(`🔍 Mutation: verifyOtpForSignup for email: ${email}`);
    try {
      // Find OTP record
      const type = "signup_email_verification";
      logger.info(`📊 Looking up OTP record for: ${email}`);
      const record = await UserOTP.findOne({ userId: email, otp, type });
      if (!record) {
        logger.warn(`⚠️ Invalid OTP for: ${email}`);
        return ApiResponse.error("Invalid OTP", 400);
      }

      // Check if expired
      const now = Date.now();
      if (record.expireAt < now) {
        logger.warn(`⚠️ OTP expired for: ${email}`);
        // Delete expired OTP
        await UserOTP.deleteOne({ _id: record._id });
        return ApiResponse.error("OTP expired", 410);
      }

      // OTP is valid, delete record
      logger.info(`✅ OTP valid, deleting record`);
      await UserOTP.deleteOne({ _id: record._id });

      // ✅ Update user in PostgreSQL
      logger.info(`💾 Updating user verification status in PostgreSQL`);
      const user = await this.userRepo.findOne({ where: { email: email } });
      if (!user) {
        logger.error(`❌ User not found: ${email}`);
        return ApiResponse.error("User not found", 404);
      }

      user.isVerified = true;
      await this.userRepo.save(user);
      logger.info(`✅ User email verified: ${email}`);

      return ApiResponse.success(undefined, "OTP verified successfully");
    } catch (error: any) {
      logger.error(
        `❌ verifyOtpForSignup error for ${email}: ${error.message}`,
        error
      );
      return ApiResponse.error(error?.message || "Internal Server Error", 500);
    }
  }

  @Mutation(() => VerifyOtpResponse)
  async SendOtpForSignup(
    @Args() { email }: sendPasswordResetEmailResponse
  ): Promise<VerifyOtpResponse> {
    try {
      await this.userService.resendEmailVerificationOtp(email);
      return ApiResponse.success(undefined, "OTP sent successfully");
    } catch (err: any) {
      return ApiResponse.error(err.message || "Failed to send OTP", 500);
    }
  }

  @Mutation(() => RefreshTokenResponse)
  async refreshToken(
    @Args() { refreshToken }: RefreshTokenArgs
  ): Promise<RefreshTokenResponse> {
    try {
      const result = await this.userService.refreshToken(refreshToken);
      return result;
    } catch (err: any) {
      logger.error("Refresh token failed:", err.message);
      throw new Error(err.message || "Failed to refresh token");
    }
  }

  @Mutation(() => BaseResponse)
  async sendPasswordResetEmail(
    @Args() { email }: SendPasswordResetEmailArgs
  ): Promise<BaseResponse> {
    try {
      await this.userService.generatePasswordResetLink(email);
      const message = responseMessage.sendPasswordResetEmail;
      return ApiResponse.success(undefined, message);
    } catch (err: any) {
      console.error("Password reset error:", err);
      return ApiResponse.error(ErrorResponse.INTERNAL_SERVER_ERROR, 500);
    }
  }
  @Query(() => VerifyTokenFullResponse)
  async verifyToken(
    @Args() { idToken }: VerifyTokenArgs
  ): Promise<VerifyTokenFullResponse> {
    logger.info(`🔍 Query: verifyToken`);
    try {
      const result = await this.userService.verifyToken(idToken);
      const data = { uid: result.uid, email: result.email };
      return ApiResponse.success(data, responseMessage.refreshToken);
    } catch (err: any) {
      logger.error(`❌ verifyToken failed: ${err.message}`, err);
      // ⚠️ Must return here
      return ApiResponse.error(
        err.message || responseMessage.failRefreshToken,
        500
      );
    }
  }

  @Query(() => UserDetailsResponse)
  async getProfile(
    @Ctx() ctx: { currentUser: UserContext | null }
  ): Promise<UserDetailsResponse> {
    logger.info(`🔍 Query: verifyToken`);
    try {
      const currentUser = ctx?.currentUser;
      // const data = { uid: result.uid, email: result.email };
      return ApiResponse.success([currentUser], responseMessage.refreshToken);
    } catch (err: any) {
      logger.error(`❌ verifyToken failed: ${err.message}`, err);
      // ⚠️ Must return here
      return ApiResponse.error(
        err.message || responseMessage.failRefreshToken,
        500
      );
    }
  }


  @Query(() => UserDetailsResponse)
  async deleteProfile(
    @Ctx() ctx: { currentUser: UserContext | null }
  ): Promise<UserDetailsResponse> {
    logger.info(`🔍 Query: verifyToken`);
    try {
      const currentUser = ctx?.currentUser;
      await this.userService.deleteUserProfile(currentUser!);
      // const data = { uid: result.uid, email: result.email };
      return ApiResponse.success([currentUser], responseMessage.refreshToken);
    } catch (err: any) {
      logger.error(`❌ verifyToken failed: ${err.message}`, err);
      // ⚠️ Must return here
      return ApiResponse.error(
        err.message || responseMessage.failRefreshToken,
        500
      );
    }
  }

  @Mutation(() => loginOrSignupWithGoogleResponse)
  async loginSignupWithGoogle(
    @Args() args: GoogleSignupArgs
  ): Promise<loginOrSignupWithGoogleResponse> {
    try {
      const data = await this.userService.loginOrSignupWithGoogle(args);


      return ApiResponse.success(data, responseMessage.UserLoginSuccess);
    } catch (err: any) {
      logger.error(`❌ .loginOrSignupWithGoogle failed: ${err.message}`, err);
      // ⚠️ Must return here
      return ApiResponse.error(
        err.message || responseMessage.failRefreshToken,
        500
      );
    }
  }

  @Mutation(() => UserDetailsResponse)
  async updateProfile(
    @Args() args: UpdateProfileInput,
    @Ctx() ctx: { currentUser: UserContext | null }
  ): Promise<UserDetailsResponse> {
    try {
      const loginUser = ctx.currentUser;
      if (!loginUser || !loginUser.isVerified) {
        throw new CustomGraphQLError("Unauthorized", HttpStatusCodes.UNAUTHORIZED);
      }

      const updateUser: UserResponseDto = await this.userService.updateProfile(loginUser.id, args);

      const userDto: UserResponseDto = {
        id: updateUser.id!,
        firstName: updateUser.firstName || "",
        lastName: updateUser.lastName || "",
        name: `${updateUser.firstName || ""} ${updateUser.lastName || ""}`.trim(),
        email: updateUser.email || "",
        username: updateUser.username || "",
        firebaseId: updateUser.firebaseId || "",
        dob: updateUser.dob || "",
        phoneNumber: updateUser.phoneNumber || "",
        isVerified: updateUser.isVerified || false,
      };

      return ApiResponse.success([userDto], "User details fetched successfully");
    } catch (error: any) {
      logger.error(`❌ updateProfile error: ${error.message}`, error);
      return ApiResponse.error("Internal Server Error", 500);
    }
  }

  @Mutation(() => BaseResponse)
  async followUser(
    @Args() { targetUserId }: FollowUserArgs,
    @Ctx() ctx: any
  ): Promise<BaseResponse> {
    try {
      const currentUser = ctx.currentUser;
      if (!currentUser) throw new Error("Unauthorized");

      const result = await this.followService.followUser(currentUser.id, targetUserId);
      return ApiResponse.success(undefined, result.message);
    } catch (error: any) {
      logger.error(`❌ followUser error: ${error.message}`);
      return ApiResponse.error(error.message || "Internal Server Error", 500);
    }
  }

  @Mutation(() => BaseResponse)
  async unfollowUser(
    @Args() { targetUserId }: FollowUserArgs,
    @Ctx() ctx: any
  ): Promise<BaseResponse> {
    try {
      const currentUser = ctx.currentUser;
      if (!currentUser) throw new Error("Unauthorized");

      const result = await this.followService.unfollowUser(currentUser.id, targetUserId);
      return ApiResponse.success(undefined, result.message);
    } catch (error: any) {
      logger.error(`❌ unfollowUser error: ${error.message}`);
      return ApiResponse.error(error.message || "Internal Server Error", 500);
    }
  }
}



